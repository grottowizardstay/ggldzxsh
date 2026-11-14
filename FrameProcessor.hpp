#pragma once
#include "support/platform.hpp"
#include <windows.h>
#include <d3d11.h>
#include <d3d11_4.h>
#include <d3dcompiler.h>
#include <wrl/client.h>
#include <array>
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <string>
using Microsoft::WRL::ComPtr;
inline void PreprocessCheck(HRESULT hr,const char* what) {
    if(FAILED(hr)){char b[32];sprintf_s(b,"0x%08X",unsigned(hr));throw std::runtime_error(std::string(what)+" failed, hr="+b);}
}
struct LetterboxInfo
{
    float ratio = 1, padX = 0, padY = 0, offsetX = 0, offsetY = 0;
    int net = 640;
    std::uint64_t frameId = 0;
    double capturedMs = 0.0, submittedMs = 0.0;
    double presentedMs = 0.0, acquiredMs = 0.0;
    std::uint32_t accumulatedFrames=0;
    float roiWidth=0, roiHeight=0;
};

// Element type of the output tensor. Narrower formats shrink the GPU copy,
// the readback and the CPU copy by 2x (Float16) or 4x (UNorm8).
enum class TensorFormat { Float32, Float16, UNorm8 };

struct FrameProcessorConfig
{
    bool profile = false;
    TensorFormat format = TensorFormat::Float32;
    // Optional cs_5_0 bytecode of kPreHLSL built offline, which skips D3DCompile at startup:
    //   fxc /T cs_5_0 /E CSMain /O3 [/D DST_T="unorm float" for UNorm8]
    const void* csBytecode = nullptr;
    size_t csBytecodeSize = 0;
    // Use an ID3D11Fence with an event when the device supports it; otherwise event queries are polled.
    bool useFence = true;
};

static const char* kPreHLSL = R"(
#ifndef DST_T
#define DST_T float
#endif
Texture2D<float4> gSrc : register(t0);
SamplerState      gSmp : register(s0);
RWBuffer<DST_T>   gDst : register(u0);
cbuffer Params : register(b0) {
    float2 gDesktopSize; float2 gRegionSize;
    float2 gRegionOffset; float2 gPad;
    float gRatio; uint gNet; float2 _pad;
};
[numthreads(8,8,1)]
void CSMain(uint3 tid : SV_DispatchThreadID) {
    if (tid.x >= gNet || tid.y >= gNet) return;
    float2 local = (float2(tid.xy) + 0.5 - gPad) / gRatio;
    float3 rgb = 114.0/255.0;
    if (all(local >= 0.0) && all(local < gRegionSize)) {
        float2 dp = gRegionOffset + local;
        rgb = gSrc.SampleLevel(gSmp, dp / gDesktopSize, 0).rgb;
    }
    uint plane = gNet*gNet, idx = tid.y*gNet + tid.x;
    gDst[idx] = rgb.r; gDst[plane+idx] = rgb.g; gDst[2*plane+idx] = rgb.b;
}
)";

static ComPtr<ID3DBlob> CompileSrc(const char* src, const char* entry, const char* target,
    const D3D_SHADER_MACRO* defines = nullptr)
{
    ComPtr<ID3DBlob> code, err;
    HRESULT hr = D3DCompile(src, strlen(src), nullptr, defines, nullptr,
        entry, target,
        D3DCOMPILE_OPTIMIZATION_LEVEL3 | D3DCOMPILE_ENABLE_STRICTNESS,
        0, &code, &err);
    if (FAILED(hr))
        throw std::runtime_error(err
            ? static_cast<const char*>(err->GetBufferPointer()) : "D3DCompile failed");
    return code;
}

class FrameProcessor
{
public:
    FrameProcessor() = default;
    FrameProcessor(const FrameProcessor&) = delete;
    FrameProcessor& operator=(const FrameProcessor&) = delete;
    ~FrameProcessor() { if (mReadyEvent) CloseHandle(mReadyEvent); }

    void Init(ID3D11Device* dev, bool profile = false)
    {
        FrameProcessorConfig cfg; cfg.profile = profile; Init(dev, cfg);
    }

    void Init(ID3D11Device* dev, const FrameProcessorConfig& cfg)
    {
        mTimingStride = cfg.profile ? 1u : 16u;
        mTimingCountdown = 0;
        mFormat = cfg.format;
        mElemBytes = cfg.format == TensorFormat::Float32 ? 4u : cfg.format == TensorFormat::Float16 ? 2u : 1u;
        mCBValid = false; mMapped = -1; mReadSeq = 0; mFenceValue = 0;
        for (auto& rb : mRead) rb.sync.pending = false;
        for (auto& s : mSharedSync) s.pending = false;

        if (cfg.csBytecode && cfg.csBytecodeSize)
            PreprocessCheck(dev->CreateComputeShader(cfg.csBytecode, cfg.csBytecodeSize, nullptr, &mCS), "CreateCS");
        else
        {
            const D3D_SHADER_MACRO unorm[] = { { "DST_T", "unorm float" }, { nullptr, nullptr } };
            auto cs = CompileSrc(kPreHLSL, "CSMain", "cs_5_0",
                cfg.format == TensorFormat::UNorm8 ? unorm : nullptr);
            PreprocessCheck(dev->CreateComputeShader(cs->GetBufferPointer(), cs->GetBufferSize(), nullptr, &mCS), "CreateCS");
        }

        D3D11_BUFFER_DESC bd{};
        bd.ByteWidth = UINT(TensorCount(640) * mElemBytes);
        bd.Usage = D3D11_USAGE_DEFAULT;
        bd.BindFlags = D3D11_BIND_UNORDERED_ACCESS;
        for (auto& tensor : mTensor)
            PreprocessCheck(dev->CreateBuffer(&bd, nullptr, &tensor), "tensor buf");

        D3D11_UNORDERED_ACCESS_VIEW_DESC ud{};
        ud.Format = cfg.format == TensorFormat::Float32 ? DXGI_FORMAT_R32_FLOAT
            : cfg.format == TensorFormat::Float16 ? DXGI_FORMAT_R16_FLOAT : DXGI_FORMAT_R8_UNORM;
        ud.ViewDimension = D3D11_UAV_DIMENSION_BUFFER;
        ud.Buffer.NumElements = UINT(TensorCount(640));
        for (size_t i = 0; i < mTensor.size(); ++i)
            PreprocessCheck(dev->CreateUnorderedAccessView(mTensor[i].Get(), &ud, &mUAV[i]), "tensor UAV");

        bd.Usage = D3D11_USAGE_STAGING; bd.BindFlags = 0;
        bd.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
        for (auto& rb : mRead) PreprocessCheck(dev->CreateBuffer(&bd, nullptr, &rb.staging), "staging");

        D3D11_BUFFER_DESC cb{};
        cb.ByteWidth = 48; cb.Usage = D3D11_USAGE_DYNAMIC;
        cb.BindFlags = D3D11_BIND_CONSTANT_BUFFER;
        cb.CPUAccessFlags = D3D11_CPU_ACCESS_WRITE;
        PreprocessCheck(dev->CreateBuffer(&cb, nullptr, &mCB), "cbuffer");

        mFence.Reset();
        if (cfg.useFence)
        {
            ComPtr<ID3D11Device5> dev5;
            if (SUCCEEDED(ComPtr<ID3D11Device>(dev).As(&dev5)) &&
                SUCCEEDED(dev5->CreateFence(0, D3D11_FENCE_FLAG_NONE, __uuidof(ID3D11Fence),
                    reinterpret_cast<void**>(mFence.ReleaseAndGetAddressOf()))))
            {
                if (!mReadyEvent) mReadyEvent = CreateEventW(nullptr, FALSE, FALSE, nullptr);
                if (!mReadyEvent) mFence.Reset();
            }
        }

        D3D11_QUERY_DESC qd{ D3D11_QUERY_EVENT, 0 };
        for (auto& rb : mRead) PreprocessCheck(dev->CreateQuery(&qd, &rb.sync.query), "query");
        for (auto& s : mSharedSync) PreprocessCheck(dev->CreateQuery(&qd, &s.query), "shared write query");
        for (auto& timing : mGpuTimes)
        {
            D3D11_QUERY_DESC disjoint{ D3D11_QUERY_TIMESTAMP_DISJOINT, 0 };
            D3D11_QUERY_DESC timestamp{ D3D11_QUERY_TIMESTAMP, 0 };
            timing.pending = false;
            timing.valid = SUCCEEDED(dev->CreateQuery(&disjoint, &timing.disjoint)) &&
                SUCCEEDED(dev->CreateQuery(&timestamp, &timing.start)) &&
                SUCCEEDED(dev->CreateQuery(&timestamp, &timing.end));
        }

        D3D11_SAMPLER_DESC sd{};
        sd.Filter = D3D11_FILTER_MIN_MAG_MIP_LINEAR;
        sd.AddressU = sd.AddressV = sd.AddressW = D3D11_TEXTURE_ADDRESS_CLAMP;
        sd.MaxLOD = D3D11_FLOAT32_MAX;
        PreprocessCheck(dev->CreateSamplerState(&sd, &mSmp), "sampler");
    }

    ID3D11Buffer* TensorBuffer(size_t slot = 0) const { return mTensor[slot].Get(); }
    TensorFormat Format() const { return mFormat; }
    // Bytes of one tensor of the given side in the configured format.
    size_t TensorBytes(int net) const { return TensorCount(net) * mElemBytes; }
    // Signalled when a submitted CPU frame becomes fetchable; null when fences are unavailable.
    HANDLE ReadyEvent() const { return mFence ? mReadyEvent : nullptr; }

    bool CanWriteSharedSlot(ID3D11DeviceContext* ctx, size_t slot)
    {
        if (slot >= mTensor.size()) return false;
        auto& s = mSharedSync[slot];
        if (!s.pending) return true;
        const HRESULT hr = Poll(ctx, s);
        if (FAILED(hr)) s.pending = false;
        PreprocessCheck(hr, "Shared preprocess fence");
        if (hr != S_OK) return false;
        s.pending = false;
        return true;
    }

    void DiscardCpuFrames() { for (auto& rb : mRead) rb.sync.pending = false; }


    void SetSharedMode(bool on) { mShared = on; }

    template<class Region>
    LetterboxInfo Submit(ID3D11DeviceContext* ctx, ID3D11ShaderResourceView* srv,
        UINT dw, UINT dh, const Region& r,
        LONG outputLeft, LONG outputTop,
        std::uint64_t frameId, double capturedMs, double submittedMs, double presentedMs, size_t slot, int net, double acquiredMs=0, std::uint32_t accumulatedFrames=0)
    {
        if (!dw || !dh || !r.width || !r.height || slot >= mTensor.size())
        {
            LetterboxInfo none{}; none.net = 0; return none;
        }
        if(net<64 || net>640) throw std::runtime_error("Invalid preprocess side");
        // Choose the readback buffer first: one nothing is waiting on, else the oldest finished frame
        // nobody fetched. If every buffer is still in flight the GPU is behind, and overwriting one would
        // lose a frame that is about to complete, so this frame is dropped instead (net = 0).
        int w = -1;
        if (!mShared)
        {
            for (int i = 0; i < int(mRead.size()) && w < 0; ++i)
                if (i != mMapped && !mRead[i].sync.pending) w = i;
            if (w < 0) for (int i = 0; i < int(mRead.size()); ++i)
            {
                if (i == mMapped || (w >= 0 && mRead[i].seq > mRead[w].seq)) continue;
                if (Poll(ctx, mRead[i].sync) != S_FALSE) w = i;
            }
            if (w < 0) { LetterboxInfo none{}; none.net = 0; return none; }
        }
        float ratio = std::min(float(net) / r.width, float(net) / r.height);
        LetterboxInfo lb{ ratio,
            (net - r.width * ratio) * .5f,
            (net - r.height * ratio) * .5f,
            float(outputLeft), float(outputTop), net };
        lb.frameId = frameId; lb.capturedMs = capturedMs; lb.submittedMs = submittedMs; lb.presentedMs=presentedMs;
        lb.acquiredMs=acquiredMs; lb.accumulatedFrames=accumulatedFrames;
        lb.roiWidth=float(r.width); lb.roiHeight=float(r.height);
        PollGpuTiming(ctx);

        float params[12] = { float(dw), float(dh), float(r.width), float(r.height),
            float(r.left), float(r.top), lb.padX, lb.padY, ratio, 0, 0, 0 };
        const UINT netU = UINT(net);
        memcpy(&params[9], &netU, sizeof(netU));
        // The parameters rarely change between frames, so only re-upload on a difference.
        if (!mCBValid || memcmp(params, mCBCache, sizeof(params)) != 0)
        {
            D3D11_MAPPED_SUBRESOURCE m{};
            PreprocessCheck(ctx->Map(mCB.Get(), 0, D3D11_MAP_WRITE_DISCARD, 0, &m), "Map CB");
            memcpy(m.pData, params, sizeof(params));
            ctx->Unmap(mCB.Get(), 0);
            memcpy(mCBCache, params, sizeof(params));
            mCBValid = true;
        }

        auto* uav = mUAV[slot].Get(); auto* cb = mCB.Get(); auto* smp = mSmp.Get();
        ctx->CSSetShader(mCS.Get(), nullptr, 0);
        ctx->CSSetShaderResources(0, 1, &srv);
        ctx->CSSetSamplers(0, 1, &smp);
        ctx->CSSetConstantBuffers(0, 1, &cb);
        ctx->CSSetUnorderedAccessViews(0, 1, &uav, nullptr);
        int timingSlot = -1;
        const bool sampleTiming = mTimingCountdown == 0;
        mTimingCountdown = sampleTiming ? mTimingStride - 1 : mTimingCountdown - 1;
        if (sampleTiming) for (size_t i = 0; i < mGpuTimes.size(); ++i)
        {
            auto& t = mGpuTimes[i];
            if (t.valid && !t.pending)
            {
                timingSlot = int(i); t.sequence = ++mGpuSequence;
                ctx->Begin(t.disjoint.Get()); ctx->End(t.start.Get());
                break;
            }
        }
        ctx->Dispatch((net + 7) / 8, (net + 7) / 8, 1);
        if (timingSlot >= 0)
        {
            auto& t = mGpuTimes[size_t(timingSlot)];
            ctx->End(t.end.Get()); ctx->End(t.disjoint.Get()); t.pending = true;
        }

        ID3D11UnorderedAccessView* nu = nullptr; ID3D11ShaderResourceView* ns = nullptr;
        ctx->CSSetUnorderedAccessViews(0, 1, &nu, nullptr);
        ctx->CSSetShaderResources(0, 1, &ns);
        ctx->CSSetShader(nullptr, nullptr, 0);

        if (mShared)
        {
            Mark(ctx, mSharedSync[slot], false);
            ctx->Flush();
            return lb;
        }

        auto& rb = mRead[size_t(w)];
        const UINT usedBytes = UINT(TensorBytes(net));
        const D3D11_BOX usedRange{ 0, 0, 0, usedBytes, 1, 1 };
        ctx->CopySubresourceRegion(rb.staging.Get(), 0, 0, 0, 0,
            mTensor[slot].Get(), 0, &usedRange);
        rb.lb = lb; rb.seq = ++mReadSeq;
        Mark(ctx, rb.sync, true);
        ctx->Flush();
        return lb;
    }

    // Maps the newest completed CPU frame without copying it. Returns null when none is ready.
    // The pointer holds TensorBytes(lb.net) bytes and stays valid until Unmap().
    const void* TryMap(ID3D11DeviceContext* ctx, LetterboxInfo& lb)
    {
        if (mMapped >= 0) return nullptr;
        std::uint64_t bound = UINT64_MAX;
        for (;;)
        {
            int best = -1;
            for (int i = 0; i < int(mRead.size()); ++i)
                if (mRead[i].sync.pending && mRead[i].seq < bound && (best < 0 || mRead[i].seq > mRead[best].seq))
                    best = i;
            if (best < 0) return nullptr;
            auto& rb = mRead[size_t(best)];
            bound = rb.seq;
            const HRESULT hr = Poll(ctx, rb.sync);
            if (FAILED(hr)) { rb.sync.pending = false; PreprocessCheck(hr, "Readback fence"); }
            if (hr != S_OK) continue;
            D3D11_MAPPED_SUBRESOURCE m{};
            const HRESULT mapped = ctx->Map(rb.staging.Get(), 0, D3D11_MAP_READ,
                D3D11_MAP_FLAG_DO_NOT_WAIT, &m);
            if (mapped == DXGI_ERROR_WAS_STILL_DRAWING) continue;
            if (FAILED(mapped)) { rb.sync.pending = false; PreprocessCheck(mapped, "Readback Map"); }
            // Delivering this frame makes every older one stale.
            for (auto& o : mRead) if (o.seq <= rb.seq) o.sync.pending = false;
            mMapped = best; lb = rb.lb;
            return m.pData;
        }
    }

    void Unmap(ID3D11DeviceContext* ctx)
    {
        if (mMapped < 0) return;
        ctx->Unmap(mRead[size_t(mMapped)].staging.Get(), 0);
        mMapped = -1;
    }

    // dst must hold TensorBytes(net) bytes; it is float data only for TensorFormat::Float32.
    bool TryFetch(ID3D11DeviceContext* ctx, void* dst, LetterboxInfo& lb)
    {
        const void* src = TryMap(ctx, lb);
        if (!src) return false;
        memcpy(dst, src, TensorBytes(lb.net));
        Unmap(ctx);
        return true;
    }

    // Like TryFetch, but sleeps until a frame is ready or timeoutMs elapses instead of returning at once.
    bool WaitFetch(ID3D11DeviceContext* ctx, void* dst, LetterboxInfo& lb, DWORD timeoutMs)
    {
        const ULONGLONG deadline = GetTickCount64() + timeoutMs;
        for (;;)
        {
            if (TryFetch(ctx, dst, lb)) return true;
            if (!HasPending()) return false;
            const ULONGLONG now = GetTickCount64();
            if (now >= deadline) return false;
            if (mFence) WaitForSingleObject(mReadyEvent, DWORD(deadline - now));
            else SwitchToThread();
        }
    }

    bool HasPending() const
    {
        for (auto& rb : mRead) if (rb.sync.pending) return true;
        return false;
    }

    double GpuMs() const { return mLastGpuMs; }
    void PollGpuTiming(ID3D11DeviceContext* ctx)
    {
        for (auto& t : mGpuTimes)
        {
            if (!t.pending) continue;
            D3D11_QUERY_DATA_TIMESTAMP_DISJOINT d{};
            UINT64 begin = 0, end = 0;
            const UINT flags = D3D11_ASYNC_GETDATA_DONOTFLUSH;
            const HRESULT hd = ctx->GetData(t.disjoint.Get(), &d, sizeof(d), flags);
            if (FAILED(hd)) { t.pending = false; t.valid = false; continue; }
            if (hd != S_OK) continue;
            const HRESULT hb = ctx->GetData(t.start.Get(), &begin, sizeof(begin), flags);
            const HRESULT he = ctx->GetData(t.end.Get(), &end, sizeof(end), flags);
            if (FAILED(hb) || FAILED(he)) { t.pending = false; t.valid = false; continue; }
            if (hb != S_OK || he != S_OK) continue;
            if (!d.Disjoint && d.Frequency && end >= begin && t.sequence > mLastGpuSequence)
            {
                mLastGpuMs = double(end - begin) * 1000.0 / double(d.Frequency);
                mLastGpuSequence = t.sequence;
            }
            t.pending = false;
        }
    }

private:
    static size_t TensorCount(int side) noexcept { return size_t(side)*side*3; }

    // Completion marker for GPU work: a fence value when fences are available, else an event query.
    struct Sync
    {
        ComPtr<ID3D11Query> query;
        UINT64 value = 0;
        bool pending = false;
    };
    void Mark(ID3D11DeviceContext* ctx, Sync& s, bool notify)
    {
        if (mFence)
        {
            ComPtr<ID3D11DeviceContext4> ctx4;
            PreprocessCheck(ComPtr<ID3D11DeviceContext>(ctx).As(&ctx4), "DeviceContext4");
            s.value = ++mFenceValue;
            PreprocessCheck(ctx4->Signal(mFence.Get(), s.value), "Fence signal");
            if (notify) PreprocessCheck(mFence->SetEventOnCompletion(s.value, mReadyEvent), "Fence event");
        }
        else ctx->End(s.query.Get());
        s.pending = true;
    }
    // S_OK once the marked work has completed, S_FALSE while it is in flight.
    HRESULT Poll(ID3D11DeviceContext* ctx, const Sync& s) const
    {
        if (mFence) return mFence->GetCompletedValue() >= s.value ? S_OK : S_FALSE;
        BOOL done = FALSE;
        const HRESULT hr = ctx->GetData(s.query.Get(), &done, sizeof(done),
            D3D11_ASYNC_GETDATA_DONOTFLUSH);
        return (hr == S_OK && !done) ? S_FALSE : hr;
    }

    struct Readback
    {
        ComPtr<ID3D11Buffer> staging;
        Sync sync;
        LetterboxInfo lb{};
        std::uint64_t seq = 0;
    };

    ComPtr<ID3D11ComputeShader>         mCS;
    std::array<ComPtr<ID3D11Buffer>, 2> mTensor;
    ComPtr<ID3D11Buffer>                mCB;
    ComPtr<ID3D11SamplerState>          mSmp;
    std::array<ComPtr<ID3D11UnorderedAccessView>, 2> mUAV;
    std::array<Sync, 2>                 mSharedSync;
    // Three buffers so a submit never has to overwrite the frame a reader is about to take.
    std::array<Readback, 3>             mRead;
    std::uint64_t                       mReadSeq = 0;
    int                                 mMapped = -1;
    ComPtr<ID3D11Fence>                 mFence;
    UINT64                              mFenceValue = 0;
    HANDLE                              mReadyEvent = nullptr;
    TensorFormat                        mFormat = TensorFormat::Float32;
    UINT                                mElemBytes = 4;
    float                               mCBCache[12] = {};
    bool                                mCBValid = false;
    bool                                mShared = false;
    struct GpuTimingSlot
    {
        ComPtr<ID3D11Query> disjoint, start, end;
        bool valid = false, pending = false;
        std::uint64_t sequence = 0;
    };
    std::array<GpuTimingSlot, 4> mGpuTimes;
    unsigned mTimingStride = 16, mTimingCountdown = 0;
    std::uint64_t mGpuSequence = 0, mLastGpuSequence = 0;
    double mLastGpuMs = -1.0;
};
