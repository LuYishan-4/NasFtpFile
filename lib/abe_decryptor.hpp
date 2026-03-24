#include <windows.h>
#include <objbase.h>
#include <string>
#include <vector>

// Chrome IElevator COM 介面定義
MIDL_INTERFACE("708860E0-F641-4cb1-957D-FA2FD964F7BC")
IElevator : public IUnknown {
public:
    virtual HRESULT STDMETHODCALLTYPE DecryptData(
        /* [size_is][in] */ const BYTE *ciphertext,
        /* [in] */ DWORD ciphertext_size,
        /* [size_is][out] */ BYTE **plaintext,
        /* [out] */ DWORD *plaintext_size) = 0;
};

// 定義 CLSID (Chrome Elevator Service)
CLSID CLSID_Elevator = {0x708860E0, 0xF641, 0x4cb1, {0x95, 0x7D, 0xFA, 0x2F, 0xD9, 0x64, 0xF7, 0xBC}};
IID IID_IElevator = {0x708860E0, 0xF641, 0x4cb1, {0x95, 0x7D, 0xFA, 0x2F, 0xD9, 0x64, 0xF7, 0xBC}};