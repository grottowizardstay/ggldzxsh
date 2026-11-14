// Compares the original FrameProcessor (bench/baseline) with the current one on the same device.
#include "support/platform.hpp"
#include <windows.h>
#include <d3d11.h>
#include <d3d11_4.h>
#include <d3dcompiler.h>
#include <dxgi.h>
#include <wrl/client.h>
#include <array>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <stdexcept>
#include <string>
#include <vector>

// The baseline declares the same names, so it is confined to a namespace.
// Every header it includes is already included above.
namespace baseline {
#include "baseline/FrameProcessor.hpp"
}
#include "../FrameProcessor.hpp"

struct Region { int left, top, width, height; };
static const UINT kW = 1920, kH = 1080;
static const Region kRoi{ 320, 60, 1280, 960 };

using Clock = std::chrono::steady_clock;
static double Ms(Clock::time_point a, Clock::time_point b) { return std::chrono::duration<double, std::milli>(b - a).count(); }
struct Stat { double med = 0, p95 = 0; };
static Stat Summarize(std::vector<double> v)
{
    if (v.empty()) return {};
    std::sort(v.begin(), v.end());
    return { v[v.size() / 2], v[std::min(v.size() - 1, v.size() * 95 / 100)] };
}

static ComPtr<ID3D11Device> gDev; static ComPtr<ID3D11DeviceContext> gCtx; static ComPtr<ID3D11ShaderResourceView> gSrv;

template<class FP> static void SubmitOne(FP& fp, int net, std::uint64_t id, size_t slot = 0)
{
    fp.Submit(gCtx.Get(), gSrv.Get(), kW, kH, kRoi, 0, 0, id, 0, 0, 0, slot, net);
}

// Polls until a frame arrives. sleepMs < 0 spins, otherwise sleeps between polls like a frame loop would;
// ev (if set) is waited on instead. Returns the duration of the successful fetch call alone.
template<class FP, class LB> static double FetchBlocking(FP& fp, void* dst, LB& lb, int sleepMs, HANDLE ev = nullptr)
{
    const auto start = Clock::now();
    for (;;)
    {
        const auto t0 = Clock::now();
        const bool ok = fp.TryFetch(gCtx.Get(), static_cast<float*>(dst), lb);
        const auto t1 = Clock::now();
        if (ok) return Ms(t0, t1);
        if (Ms(start, t1) > 10000) throw std::runtime_error("readback timed out");
        if (ev) WaitForSingleObject(ev, 100);
        else if (sleepMs >= 0) Sleep(DWORD(sleepMs));
    }
}

static float HalfToFloat(std::uint16_t h)
{
    const int e = (h >> 10) & 31, m = h & 1023;
    const float v = e == 0 ? std::ldexp(float(m), -24) : std::ldexp(float(m + 1024), e - 25);
    return (h & 0x8000) ? -v : v;
}

struct Row { std::string name; Stat roundTrip, fetch; };
template<class FP, class LB> static Row Latency(const char* name, FP& fp, int net, int sleepMs, HANDLE ev, int n)
{
    std::vector<unsigned char> dst(size_t(net) * net * 3 * 4);
    std::vector<double> rt, ft; LB lb{};
    for (int i = 0; i < n + 20; ++i)
    {
        const auto t0 = Clock::now();
        SubmitOne(fp, net, std::uint64_t(i));
        const double f = FetchBlocking(fp, dst.data(), lb, sleepMs, ev);
        if (i >= 20) { rt.push_back(Ms(t0, Clock::now())); ft.push_back(f); }
    }
    return { name, Summarize(rt), Summarize(ft) };
}

template<class FP, class LB> static Stat SubmitCost(FP& fp, int net, int n)
{
    std::vector<unsigned char> dst(size_t(net) * net * 3 * 4);
    std::vector<double> v; LB lb{};
    for (int i = 0; i < n; ++i)
    {
        const auto t0 = Clock::now();
        SubmitOne(fp, net, std::uint64_t(i));
        v.push_back(Ms(t0, Clock::now()) * 1000.0);
        FetchBlocking(fp, dst.data(), lb, -1);
    }
    return Summarize(v);
}

// A paced capture loop that makes one non-blocking fetch attempt per tick, either right after the
// submit or just before the next one. Counts the frames that reach the CPU and how stale they are.
struct Delivery { int delivered = 0; double age = 0; };
template<class FP, class LB> static Delivery Paced(FP& fp, int net, double periodMs, bool fetchFirst, int rounds)
{
    std::vector<unsigned char> buf(size_t(net) * net * 3 * 4);
    float* dst = static_cast<float*>(static_cast<void*>(buf.data()));
    LB lb{}; Delivery d; std::uint64_t id = 0;
    const auto t0 = Clock::now();
    for (int r = 0; r < rounds; ++r)
    {
        bool got = false;
        if (fetchFirst) got = fp.TryFetch(gCtx.Get(), dst, lb);
        SubmitOne(fp, net, ++id);
        if (!fetchFirst) got = fp.TryFetch(gCtx.Get(), dst, lb);
        if (got) { ++d.delivered; d.age += double(id - lb.frameId); }
        while (Ms(t0, Clock::now()) < periodMs * (r + 1)) Sleep(1);
    }
    if (d.delivered) d.age /= d.delivered;
    Sleep(50); fp.DiscardCpuFrames();
    return d;
}

// CPU bilinear letterbox of the source pattern, to check the GPU output independently of the baseline.
static double MaxErrVsCpu(const std::vector<std::uint32_t>& px, const std::vector<float>& out, int net)
{
    const float ratio = std::min(float(net) / kRoi.width, float(net) / kRoi.height);
    const float padX = (net - kRoi.width * ratio) * .5f, padY = (net - kRoi.height * ratio) * .5f;
    const size_t plane = size_t(net) * net;
    double worst = 0;
    for (int y = 0; y < net; ++y) for (int x = 0; x < net; ++x)
    {
        const float lx = (x + 0.5f - padX) / ratio, ly = (y + 0.5f - padY) / ratio;
        float rgb[3] = { 114 / 255.f, 114 / 255.f, 114 / 255.f };
        if (lx >= 0 && ly >= 0 && lx < kRoi.width && ly < kRoi.height)
        {
            const float u = kRoi.left + lx - 0.5f, v = kRoi.top + ly - 0.5f;
            const float fu = std::floor(u), fv = std::floor(v), ax = u - fu, ay = v - fv;
            auto at = [&](int tx, int ty, int shift) {
                tx = std::clamp(tx, 0, int(kW) - 1); ty = std::clamp(ty, 0, int(kH) - 1);
                return float((px[size_t(ty) * kW + tx] >> shift) & 255) / 255.f; };
            for (int c = 0; c < 3; ++c)
            {
                const int s = 16 - 8 * c, x0 = int(fu), y0 = int(fv);
                rgb[c] = (at(x0, y0, s) * (1 - ax) + at(x0 + 1, y0, s) * ax) * (1 - ay)
                       + (at(x0, y0 + 1, s) * (1 - ax) + at(x0 + 1, y0 + 1, s) * ax) * ay;
            }
        }
        for (int c = 0; c < 3; ++c)
            worst = std::max(worst, double(std::fabs(out[c * plane + size_t(y) * net + x] - rgb[c])));
    }
    return worst;
}

int main(int argc, char** argv)
{
    try
    {
        const int n = argc > 1 ? atoi(argv[1]) : 300;
        const D3D_FEATURE_LEVEL want = D3D_FEATURE_LEVEL_11_0;
        HRESULT hr = D3D11CreateDevice(nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr, 0, &want, 1, D3D11_SDK_VERSION, &gDev, nullptr, &gCtx);
        if (FAILED(hr)) hr = D3D11CreateDevice(nullptr, D3D_DRIVER_TYPE_WARP, nullptr, 0, &want, 1, D3D11_SDK_VERSION, &gDev, nullptr, &gCtx);
        PreprocessCheck(hr, "D3D11CreateDevice");
        {
            ComPtr<IDXGIDevice> dx; ComPtr<IDXGIAdapter> ad; DXGI_ADAPTER_DESC desc{};
            if (SUCCEEDED(gDev.As(&dx)) && SUCCEEDED(dx->GetAdapter(&ad)) && SUCCEEDED(ad->GetDesc(&desc)))
                printf("adapter: %ls\n", desc.Description);
        }

        std::vector<std::uint32_t> px(size_t(kW) * kH);
        for (UINT y = 0; y < kH; ++y) for (UINT x = 0; x < kW; ++x)
            px[size_t(y) * kW + x] = 0xFF000000u | ((x * 255 / kW) << 16) | ((y * 255 / kH) << 8) | ((x ^ y) & 255);
        D3D11_TEXTURE2D_DESC td{}; td.Width = kW; td.Height = kH; td.MipLevels = td.ArraySize = 1;
        td.Format = DXGI_FORMAT_B8G8R8A8_UNORM; td.SampleDesc.Count = 1; td.Usage = D3D11_USAGE_IMMUTABLE; td.BindFlags = D3D11_BIND_SHADER_RESOURCE;
        D3D11_SUBRESOURCE_DATA init{ px.data(), kW * 4, 0 };
        ComPtr<ID3D11Texture2D> tex;
        PreprocessCheck(gDev->CreateTexture2D(&td, &init, &tex), "source texture");
        PreprocessCheck(gDev->CreateShaderResourceView(tex.Get(), nullptr, &gSrv), "source SRV");

        auto cfg = [](TensorFormat f, bool fence) { FrameProcessorConfig c; c.format = f; c.useFence = fence; return c; };
        baseline::FrameProcessor base; base.Init(gDev.Get());
        FrameProcessor f32q, f32, f16, u8;
        f32q.Init(gDev.Get(), cfg(TensorFormat::Float32, false));
        f32.Init(gDev.Get(), cfg(TensorFormat::Float32, true));
        f16.Init(gDev.Get(), cfg(TensorFormat::Float16, true));
        u8.Init(gDev.Get(), cfg(TensorFormat::UNorm8, true));
        printf("fence+event sync: %s\n\n", f32.ReadyEvent() ? "available" : "unavailable (falls back to polled queries)");

        // 1. Output equivalence
        for (int net : { 640, 320, 65 })
        {
            const size_t count = size_t(net) * net * 3;
            std::vector<float> ref(count), a(count); std::vector<std::uint16_t> h(count); std::vector<std::uint8_t> b(count);
            baseline::LetterboxInfo blb{}; LetterboxInfo lb{};
            SubmitOne(base, net, 1); FetchBlocking(base, ref.data(), blb, -1);
            SubmitOne(f32, net, 1); FetchBlocking(f32, a.data(), lb, -1);
            SubmitOne(f16, net, 1); FetchBlocking(f16, h.data(), lb, -1);
            SubmitOne(u8, net, 1); FetchBlocking(u8, b.data(), lb, -1);
            double e16 = 0, e8 = 0;
            for (size_t i = 0; i < count; ++i)
            {
                e16 = std::max(e16, double(std::fabs(HalfToFloat(h[i]) - ref[i])));
                e8 = std::max(e8, double(std::fabs(b[i] / 255.0f - ref[i])));
            }
            const bool same = memcmp(ref.data(), a.data(), count * sizeof(float)) == 0;
            // GPU filtering uses limited sub-texel precision, so allow a little slack against the CPU reference.
            const double ecpu = MaxErrVsCpu(px, a, net);
            const bool ok = same && e16 < 1e-3 && e8 < 0.51 / 255 && ecpu < 3.0 / 255 && lb.ratio == blb.ratio && lb.padY == blb.padY;
            printf("[%s] net %3d: float32 %s baseline, %.2f/255 off CPU reference; float16 max err %.2e; unorm8 max err %.2f/255\n",
                ok ? "PASS" : "FAIL", net, same ? "bit-identical to" : "DIFFERS from", ecpu * 255, e16, e8 * 255);
            if (!ok) return 1;
        }

        // 2. Startup
        {
            auto time = [&](auto&& fn) { std::vector<double> v; for (int i = 0; i < 5; ++i) { const auto t0 = Clock::now(); fn(); v.push_back(Ms(t0, Clock::now())); } return Summarize(v).med; };
            const double tb = time([&] { baseline::FrameProcessor p; p.Init(gDev.Get()); });
            const double tn = time([&] { FrameProcessor p; p.Init(gDev.Get()); });
            auto blob = CompileSrc(kPreHLSL, "CSMain", "cs_5_0");
            FrameProcessorConfig pc; pc.csBytecode = blob->GetBufferPointer(); pc.csBytecodeSize = blob->GetBufferSize();
            const double tp = time([&] { FrameProcessor p; p.Init(gDev.Get(), pc); });
            printf("\nInit (median of 5): baseline %.2f ms | new, runtime compile %.2f ms | new, precompiled bytecode %.2f ms\n", tb, tn, tp);
        }

        for (int net : { 640, 320 })
        {
            printf("\n== net %d, %d frames per row ==\n", net, n);
            const Stat sb = SubmitCost<baseline::FrameProcessor, baseline::LetterboxInfo>(base, net, n);
            const Stat sq = SubmitCost<FrameProcessor, LetterboxInfo>(f32q, net, n);
            const Stat sf = SubmitCost<FrameProcessor, LetterboxInfo>(f32, net, n);
            printf("Submit CPU cost, median/p95 us: baseline %.1f/%.1f | new (queries) %.1f/%.1f | new (fence) %.1f/%.1f\n",
                sb.med, sb.p95, sq.med, sq.p95, sf.med, sf.p95);

            std::vector<Row> rows;
            rows.push_back(Latency<baseline::FrameProcessor, baseline::LetterboxInfo>("baseline f32, spin-poll", base, net, -1, nullptr, n));
            rows.push_back(Latency<baseline::FrameProcessor, baseline::LetterboxInfo>("baseline f32, poll every 1 ms", base, net, 1, nullptr, n));
            rows.push_back(Latency<FrameProcessor, LetterboxInfo>("new f32, poll every 1 ms", f32q, net, 1, nullptr, n));
            rows.push_back(Latency<FrameProcessor, LetterboxInfo>("new f32, event wait", f32, net, 1, f32.ReadyEvent(), n));
            rows.push_back(Latency<FrameProcessor, LetterboxInfo>("new f16, event wait", f16, net, 1, f16.ReadyEvent(), n));
            rows.push_back(Latency<FrameProcessor, LetterboxInfo>("new u8,  event wait", u8, net, 1, u8.ReadyEvent(), n));
            printf("%-32s %12s %12s %12s %12s\n", "submit -> data on CPU", "median ms", "p95 ms", "fetch med ms", "fetch p95 ms");
            for (auto& r : rows) printf("%-32s %12.3f %12.3f %12.3f %12.3f\n", r.name.c_str(), r.roundTrip.med, r.roundTrip.p95, r.fetch.med, r.fetch.p95);

            struct Case { const char* name; double periodMs; bool fetchFirst; };
            for (const Case& c : { Case{ "16 ms tick, fetch right after submit", 16, false }, Case{ "4 ms tick, fetch before submit", 4, true } })
            {
                const Delivery db = Paced<baseline::FrameProcessor, baseline::LetterboxInfo>(base, net, c.periodMs, c.fetchFirst, n);
                const Delivery dn = Paced<FrameProcessor, LetterboxInfo>(f32, net, c.periodMs, c.fetchFirst, n);
                const Delivery du = Paced<FrameProcessor, LetterboxInfo>(u8, net, c.periodMs, c.fetchFirst, n);
                printf("%-38s frames delivered of %d (mean age in frames): baseline %d (%.1f) | new f32 %d (%.1f) | new u8 %d (%.1f)\n",
                    c.name, n, db.delivered, db.age, dn.delivered, dn.age, du.delivered, du.age);
            }
        }
        return 0;
    }
    catch (const std::exception& e) { fprintf(stderr, "error: %s\n", e.what()); return 2; }
}
