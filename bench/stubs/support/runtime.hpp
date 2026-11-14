#pragma once
// Benchmark stand-in for the application's runtime header: the standard headers, constants and
// globals ObjectDetector expects, plus inert C++/WinRT and Windows ML types so the WinML code
// path compiles. None of the WinML stand-ins do anything.
#include <windows.h>
#include <algorithm>
#include <array>
#include <atomic>
#include <climits>
#include <cmath>
#include <condition_variable>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>
#include "support/worker_guard.hpp"
#include "support/diagnostics.hpp"

#ifndef BENCH_NUM_CLASSES
#define BENCH_NUM_CLASSES 80
#endif
#ifndef BENCH_DECODE_CLASS
#define BENCH_DECODE_CLASS -1
#endif
constexpr int kNetMax = 640;
constexpr size_t kTensorFloatsMax = size_t(kNetMax) * kNetMax * 3;
constexpr size_t TensorFloatsFor(int side) { return size_t(side) * size_t(side) * 3; }
constexpr int kNumClasses = BENCH_NUM_CLASSES;
constexpr int kDecodeClass = BENCH_DECODE_CLASS;
constexpr bool kModelOutputHasVerifiedNms = false;
inline std::atomic<int> gOutCh{ 0 }, gOutAnchors{ 0 }, gNetSize{ kNetMax };
inline std::atomic<float> gDecodeConf{ 0.25f };

struct IMemoryBufferByteAccess { HRESULT GetBuffer(uint8_t**, uint32_t*) { return E_NOTIMPL; } };

namespace winrt {
struct hstring { hstring() = default; hstring(const wchar_t*) {} };
inline std::string to_string(const hstring&) { return {}; }
struct hresult { int32_t value = 0; operator int32_t() const { return value; } };
struct hresult_error { hstring message() const { return {}; } hresult code() const { return {}; } };
enum class apartment_type { multi_threaded };
inline void init_apartment(apartment_type) {}
inline void uninit_apartment() {}
inline void check_hresult(HRESULT hr) { if (FAILED(hr)) throw hresult_error{}; }
template<class T> struct array_view { array_view(T*, T*) {} };
}

namespace WinML {
struct ShapeView { uint32_t Size() const { return 0; } int64_t GetAt(uint32_t) const { return 0; } };
struct TensorFeatureDescriptor { explicit operator bool() const { return false; } ShapeView Shape() const { return {}; } };
struct Feature { winrt::hstring Name() const { return {}; } template<class T> T try_as() const { return T{}; } };
struct FeatureList { Feature GetAt(uint32_t) const { return {}; } };
struct LearningModel {
    static LearningModel LoadFromFilePath(const std::wstring&) { throw winrt::hresult_error{}; }
    FeatureList InputFeatures() const { return {}; }
    FeatureList OutputFeatures() const { return {}; }
};
enum class LearningModelDeviceKind { DirectXHighPerformance, Cpu };
struct LearningModelDevice { explicit LearningModelDevice(LearningModelDeviceKind) {} };
struct MemoryReference { template<class T> T* as() const { return nullptr; } };
struct TensorFloat {
    static TensorFloat CreateFromArray(const std::vector<int64_t>&, winrt::array_view<const float>) { return {}; }
    ShapeView Shape() const { return {}; }
    MemoryReference CreateReference() const { return {}; }
};
struct OutputValue { template<class T> T as() const { return T{}; } };
struct OutputMap { OutputValue Lookup(const winrt::hstring&) const { return {}; } };
struct EvaluationResult { OutputMap Outputs() const { return {}; } };
struct LearningModelBinding;
struct LearningModelSession {
    LearningModelSession(std::nullptr_t) {}
    LearningModelSession(const LearningModel&, const LearningModelDevice&) {}
    EvaluationResult Evaluate(const LearningModelBinding&, const wchar_t*) const { return {}; }
};
struct LearningModelBinding {
    explicit LearningModelBinding(const LearningModelSession&) {}
    void Clear() {}
    void Bind(const winrt::hstring&, const TensorFloat&) {}
};
}
