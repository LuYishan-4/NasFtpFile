// main.cpp
#include <iostream>
#include <vector>
#include "abe_decryptor.hpp"

// 模擬從資料庫讀取的 v20 加密資料
// 真實使用時，請從 SQLite 的 password_value 欄位取出 Blob
std::vector<uint8_t> GetSampleEncryptedData() {
    // 這裡應填入以 'v20' 開頭的原始密文位元組
    return { 0x76, 0x32, 0x30, ... }; 
}

int main() {
    std::cout << "--- Chrome ABE Decryptor (C++ Version) ---" << std::endl;

    // 1. 取得密文
    std::vector<uint8_t> ciphertext = GetSampleEncryptedData();

    if (ciphertext.empty()) {
        std::cout << "[!] 沒有輸入資料。" << std::endl;
        return 1;
    }

    // 2. 執行解密
    std::string decrypted = ABEDecryptor::DecryptV20(ciphertext);

    // 3. 輸出結果
    if (decrypted.find("ERROR") != std::string::npos) {
        std::cout << "[解密失敗] " << decrypted << std::endl;
        std::cout << "提示：如果不使用注入，程式必須以管理員權限執行，且可能仍被 Chrome 拒絕。" << std::endl;
    } else {
        std::cout << "[解密成功] 明文密碼: " << decrypted << std::endl;
    }

    return 0;
}