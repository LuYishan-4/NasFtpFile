#include <windows.h>
#include <objbase.h>

// 根據你上傳的 browser_config.hpp 定義的 IElevator 介面
struct __declspec(uuid("708860E0-F641-4cb1-957D-FA2FD964F7BC")) IElevator : public IUnknown {
    virtual HRESULT STDMETHODCALLTYPE DecryptData(
        const BYTE* ciphertext, DWORD ciphertext_size,
        BYTE** plaintext, DWORD* plaintext_size) = 0;
};

extern "C" __declspec(dllexport) int __stdcall DecryptABE(
    const BYTE* cipher, int cipher_len, char* out_plain, int* out_len) {
    
    // 初始化 COM 環境
    HRESULT hr = CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
    if (FAILED(hr)) return -1;

    IElevator* pElevator = NULL;
    // 建立 Chrome Elevator Service 實例
    hr = CoCreateInstance(__uuidof(IElevator), NULL, CLSCTX_LOCAL_SERVER, __uuidof(IElevator), (void**)&pElevator);

    int status = -2; 
    if (SUCCEEDED(hr)) {
        BYTE* plaintext = NULL;
        DWORD plaintext_size = 0;

        // 核心：呼叫 ABE 解密
        hr = pElevator->DecryptData(cipher, (DWORD)cipher_len, &plaintext, &plaintext_size);

        if (SUCCEEDED(hr)) {
            if ((int)plaintext_size < *out_len) {
                memcpy(out_plain, plaintext, plaintext_size);
                *out_len = (int)plaintext_size;
                status = 0; // 成功
            } else {
                status = -3; // 緩衝區不足
            }
            CoTaskMemFree(plaintext);
        } else {
            status = (int)hr; // 傳回 HRESULT 錯誤碼
        }
        pElevator->Release();
    }
    CoUninitialize();
    return status;
}