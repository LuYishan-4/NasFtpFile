import os
import json
import base64
import sqlite3
import shutil
import re
import pandas as pd
from Cryptodome.Cipher import AES
from win32 import win32crypt

CHROME_USER_DATA = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data")
LOCAL_STATE_PATH = os.path.join(CHROME_USER_DATA, "Local State")
TEMP_DB = "chrome_temp_vault.db"

def get_master_key():
    try:
        if not os.path.exists(LOCAL_STATE_PATH):
            print(f"error: {LOCAL_STATE_PATH}")
            return None
            
        with open(LOCAL_STATE_PATH, "r", encoding="utf-8") as f:
            local_state = json.load(f)
            
        # 取得加密金鑰並移除 'DPAPI' 前綴 (5 bytes)
        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
        # 使用 Windows DPAPI 解出真正的 AES 金鑰
        return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    except Exception as e:
        print(f"[錯誤] 無法讀取主金鑰: {e}")
        return None

def clean_for_excel(text):
    """移除會導致 Excel 崩潰的非法字元 (如 \x00, \x01 等控制字元)"""
    if not isinstance(text, str): return text
    # 移除 ASCII 0-31 (除了換行符號)，解決 '鈑' 等 Excel 無法處理的字元問題
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

def decrypt_password(ciphertext, key):
    """AES-GCM 多層次解密邏輯 (支援 v10 / v20)"""
    if not ciphertext or len(ciphertext) < 15: 
        return ""
    
    # 1. 嘗試 Chrome 80+ 的 AES-GCM 解密
    try:
        if ciphertext[:3] in [b'v10', b'v20']:
            # 切分資料：標籤(3)|IV(12)|密文(n)|Tag(16)
            iv = ciphertext[3:15]
            payload = ciphertext[15:-16]
            tag = ciphertext[-16:]
            
            cipher = AES.new(key, AES.MODE_GCM, iv)
            # 使用解密並驗證 Tag
            decrypted = cipher.decrypt_and_verify(payload, tag)
            return clean_for_excel(decrypted.decode('utf-8', errors='ignore').strip())
    except Exception:
        pass

    # 2. 嘗試舊版 Windows DPAPI 直接解密 (相容處理)
    try:
        decrypted = win32crypt.CryptUnprotectData(ciphertext, None, None, None, 0)[1]
        return clean_for_excel(decrypted.decode('utf-8', errors='ignore').strip())
    except Exception:
        return "(解密失敗：可能受到 App-Bound ABE 保護)"

def main():
    print("=== Chrome 全設定檔密碼提取工具 ===")
    
    master_key = get_master_key()
    if not master_key:
        return

    # 自動偵測 User Data 下所有的 Profile 資料夾
    if not os.path.exists(CHROME_USER_DATA):
        print(f"[錯誤] 找不到 Chrome 資料夾於: {CHROME_USER_DATA}")
        return

    profiles = [d for d in os.listdir(CHROME_USER_DATA) 
                if d == "Default" or d.startswith("Profile")]
    
    all_results = []
    print(f"偵測到 {len(profiles)} 個使用者設定檔，開始掃描...")

    for profile in profiles:
        db_path = os.path.join(CHROME_USER_DATA, profile, "Login Data")
        if not os.path.exists(db_path):
            continue
        
        print(f" -> 正在處理: {profile}")
        
        # 複製資料庫副本，防止資料庫被 Chrome 佔用而報錯
        try:
            shutil.copy2(db_path, TEMP_DB)
            conn = sqlite3.connect(TEMP_DB)
            cursor = conn.cursor()
            
            # 讀取網址、帳號、加密後的密碼
            cursor.execute("SELECT action_url, username_value, password_value FROM logins")
            
            for url, user, cryp_pass in cursor.fetchall():
                if user or url:
                    pwd = decrypt_password(cryp_pass, master_key)
                    all_results.append({
                        "設定檔 (Profile)": profile,
                        "網址 (URL)": url,
                        "使用者名稱": user,
                        "密碼": pwd
                    })
            
            conn.close()
        except Exception as e:
            print(f"    [警告] 讀取 {profile} 時發生錯誤: {e}")
        finally:
            if os.path.exists(TEMP_DB):
                os.remove(TEMP_DB)

    # 將結果匯出至 Excel
    if all_results:
        df = pd.DataFrame(all_results)
        output_file = "Chrome_Passwords_Report.xlsx"
        
        try:
            df.to_excel(output_file, index=False)
            print("-" * 45)
            print(f"成功！總計提取 {len(all_results)} 筆資料。")
            print(f"結果檔案已存至: {os.path.abspath(output_file)}")
        except Exception as e:
            print(f"[錯誤] 無法儲存 Excel: {e}")
            # 如果 Excel 失敗，嘗試存成 CSV 作為備案
            df.to_csv("Chrome_Passwords_Backup.csv", index=False, encoding="utf-8-sig")
    else:
        print("未發現任何密碼資料。")

if __name__ == "__main__":
    main()