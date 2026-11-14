#pragma once
// Benchmark stand-in for the application's inference backend interface. No backend is ever created.
#include <d3d11.h>
#include <memory>
#include <string>
#include <vector>

struct BackendStageTiming { double preMs = 0, runMs = 0, postMs = 0; };
struct InferenceOutputView { const float* data = nullptr; size_t count = 0; };

struct IInferenceBackend {
    virtual ~IInferenceBackend() = default;
    virtual const char* Name() const = 0;
    virtual std::string Diagnostics() const = 0;
    virtual int InputSide() const = 0;
    virtual bool SupportsSharedInput() const = 0;
    virtual bool BindSharedInputs(ID3D11Device*, void**, int, std::string&) = 0;
    virtual bool BindSharedInput(ID3D11Device*, void*, std::string&) = 0;
    virtual void UnbindSharedInput() = 0;
    virtual bool Run(const float*, std::vector<float>&, int&, int&, std::string&) = 0;
    virtual bool RunView(const float*, std::vector<float>&, InferenceOutputView&, int&, int&, std::string&) = 0;
    virtual bool RunSharedSlot(size_t, std::vector<float>&, int&, int&, std::string&) = 0;
    virtual bool RunSharedSlotView(size_t, std::vector<float>&, InferenceOutputView&, int&, int&, std::string&) = 0;
    virtual BackendStageTiming LastStageTiming() const = 0;
};

inline std::unique_ptr<IInferenceBackend> CreateInferenceBackend(const std::wstring&, int, std::string&) { return nullptr; }
inline bool BackendPerfEnvFlag(const wchar_t*) { return false; }
inline bool BackendIsEngineFile(const std::wstring&) { return false; }
inline std::string BackendNarrow(const std::wstring&) { return {}; }
