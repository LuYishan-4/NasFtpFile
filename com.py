import shutil
import sqlite3
import os
import pandas as pd

# Chrome 登入資料檔案路徑
chrome_path_login_db = "D:\\Login Data"
temp_db = "Loginvault.db"
output_excel = "Chrome_Passwords_Export.xlsx"

try:
    # 1. 將 Chrome 的資料庫複製一份到當前目錄（避免檔案被佔用）
    shutil.copy2(chrome_path_login_db, temp_db)

    # 2. 連結到 SQLite 資料庫
    conn = sqlite3.connect(temp_db)

    # 3. 使用 Pandas 直接執行 SQL 並讀取成表格資料
    query = "SELECT action_url, username_value, password_value FROM logins"
    df = pd.read_sql_query(query, conn)

    # 4. 重新命名欄位，讓 Excel 表格更易讀
    df.columns = ["網址 (URL)", "使用者名稱 (Username)", "加密密碼 (Ciphertext)"]

    # 5. 匯出為 Excel 檔案
    df.to_excel(output_excel, index=False)
    
    print(f"成功！資料已打包至：{os.path.abspath(output_excel)}")

except Exception as e:
    print(f"執行過程中發生錯誤：{e}")

finally:
    # 6. 關閉資料庫連線並刪除暫存檔
    if 'conn' in locals():
        conn.close()
    if os.path.exists(temp_db):
        os.remove(temp_db)
        print("暫存資料庫已清理。")