// Compares the original ObjectDetector decoder (bench/baseline/detector) with the current one on
// synthetic model outputs. Only decoding and suppression run; no model or backend is loaded.
#include "support/platform.hpp"
#include "support/runtime.hpp"
#include "support/detection.hpp"
#include "support/timing.hpp"
#include "FrameProcessor.hpp"
#include "support/inference_backend.hpp"
#include "support/model_contract.hpp"
#include <chrono>
#include <cstring>
#include <random>

// Decode is private in both versions. The baseline sources are compiled with the class renamed,
// so both can live in one program.
#define private public
#define ObjectDetector BaselineObjectDetector
#include "baseline/detector/ObjectDetector.hpp"
#undef ObjectDetector
#include "../ObjectDetector.hpp"
#undef private

struct Anchor { float cx, cy, w, h, obj; std::vector<float> cls; };

// Mostly background anchors with low scores, plus `objects` clusters of overlapping confident ones.
static std::vector<Anchor> MakeAnchors(int count, int objects, bool dirty, unsigned seed)
{
    std::mt19937 rng(seed);
    std::uniform_real_distribution<float> uni(0.f, 1.f);
    std::vector<Anchor> a(static_cast<size_t>(count));
    for (auto& v : a) {
        v = { uni(rng) * 640, uni(rng) * 640, 8 + uni(rng) * 120, 8 + uni(rng) * 120, uni(rng) * 0.1f, {} };
        v.cls.resize(kNumClasses);
        for (auto& s : v.cls) s = uni(rng) * 0.1f;
    }
    for (int o = 0; o < objects; ++o) {
        const float cx = 40 + uni(rng) * 560, cy = 120 + uni(rng) * 400, w = 20 + uni(rng) * 100, h = 20 + uni(rng) * 100;
        const int cls = int(uni(rng) * kNumClasses) % kNumClasses;
        for (int k = 0; k < 6; ++k) {
            auto& v = a[size_t(uni(rng) * (count - 1))];
            v.cx = cx + uni(rng) * 4; v.cy = cy + uni(rng) * 4; v.w = w + uni(rng) * 4; v.h = h + uni(rng) * 4;
            v.obj = 0.7f + uni(rng) * 0.3f; v.cls[size_t(cls)] = 0.5f + uni(rng) * 0.5f;
        }
    }
    if (dirty) for (int k = 0; k < count / 20; ++k) {
        auto& v = a[size_t(uni(rng) * (count - 1))];
        const float bad[] = { std::numeric_limits<float>::quiet_NaN(), std::numeric_limits<float>::infinity(), -1.f, 2.f, 1.0005f };
        const float value = bad[k % 5];
        switch (k % 4) { case 0: v.cls[size_t(k) % v.cls.size()] = value; break; case 1: v.obj = value; break; case 2: v.w = value; break; default: v.cx = value; }
    }
    return a;
}

struct Output { std::vector<float> data; int d1 = 0, d2 = 0; };
static Output Pack(const std::vector<Anchor>& a, bool objectness, bool anchorsFirst)
{
    const int first = objectness ? 5 : 4, ch = first + kNumClasses, n = int(a.size());
    Output out; out.data.resize(size_t(ch) * size_t(n)); out.d1 = anchorsFirst ? n : ch; out.d2 = anchorsFirst ? ch : n;
    auto at = [&](int c, int i) -> float& { return anchorsFirst ? out.data[size_t(i) * ch + c] : out.data[size_t(c) * n + i]; };
    for (int i = 0; i < n; ++i) {
        at(0, i) = a[i].cx; at(1, i) = a[i].cy; at(2, i) = a[i].w; at(3, i) = a[i].h;
        if (objectness) at(4, i) = a[i].obj;
        for (int c = 0; c < kNumClasses; ++c) at(first + c, i) = a[i].cls[size_t(c)];
    }
    return out;
}
static Output PackNms(int rows, unsigned seed)
{
    std::mt19937 rng(seed); std::uniform_real_distribution<float> uni(0.f, 1.f);
    Output out; out.d1 = rows; out.d2 = 6; out.data.resize(size_t(rows) * 6);
    for (int i = 0; i < rows; ++i) {
        float* r = &out.data[size_t(i) * 6];
        r[0] = uni(rng) * 500; r[1] = 100 + uni(rng) * 400; r[2] = r[0] + 10 + uni(rng) * 100; r[3] = r[1] + 10 + uni(rng) * 100;
        r[4] = uni(rng); r[5] = float(int(uni(rng) * kNumClasses) % kNumClasses);
    }
    return out;
}

static bool gFailed = false;
static void Run(const char* name, const Output& out, float conf, int iterations)
{
    using Clock = std::chrono::steady_clock;
    LetterboxInfo lb{}; lb.ratio = 0.5f; lb.padX = 0; lb.padY = 80; lb.offsetX = 320; lb.offsetY = 60; lb.net = 640;
    gDecodeConf.store(conf);
    BaselineObjectDetector base; ObjectDetector cur;
    std::vector<double> tb, tc;
    for (int i = 0; i < iterations + 10; ++i) {
        auto t0 = Clock::now(); base.Decode(out.data.data(), out.d1, out.d2, lb);
        auto t1 = Clock::now(); cur.Decode(out.data.data(), out.d1, out.d2, lb);
        auto t2 = Clock::now();
        if (i >= 10) { tb.push_back(std::chrono::duration<double, std::micro>(t1 - t0).count()); tc.push_back(std::chrono::duration<double, std::micro>(t2 - t1).count()); }
    }
    const auto& b = base.mDecodeOutput; const auto& c = cur.mDecodeOutput;
    const bool same = b.size() == c.size() && (b.empty() || std::memcmp(b.data(), c.data(), b.size() * sizeof(Detection)) == 0)
        && std::strcmp(base.LayoutName(), cur.LayoutName()) == 0;
    if (!same) gFailed = true;
    std::sort(tb.begin(), tb.end()); std::sort(tc.begin(), tc.end());
    const double mb = tb[tb.size() / 2], mc = tc[tc.size() / 2];
    printf("%-34s %-9s conf %.2f  %3zu kept  baseline %8.1f us  new %8.1f us  %5.2fx  %s\n",
        name, cur.LayoutName(), conf, c.size(), mb, mc, mb / mc, same ? "identical" : "DIFFERENT");
}

int main(int argc, char** argv)
{
    const int n = argc > 1 ? atoi(argv[1]) : 300;
    printf("classes %d, decode class %d, median of %d decodes\n", kNumClasses, kDecodeClass, n);
    const auto v8 = MakeAnchors(8400, 40, false, 1), v5 = MakeAnchors(25200, 40, false, 2);
    const auto dirty8 = MakeAnchors(8400, 40, true, 3), dirty5 = MakeAnchors(25200, 40, true, 4);
    Run("no objectness, [C,A] 8400", Pack(v8, false, false), 0.25f, n);
    Run("no objectness, [A,C] 8400", Pack(v8, false, true), 0.25f, n);
    Run("objectness, [C,A] 25200", Pack(v5, true, false), 0.25f, n);
    Run("objectness, [A,C] 25200", Pack(v5, true, true), 0.25f, n);
    Run("low threshold, [C,A] 8400", Pack(v8, false, false), 0.05f, n);
    Run("low threshold, [A,C] 8400", Pack(v8, false, true), 0.05f, n);
    Run("NaN/inf/out-of-range, [C,A] 8400", Pack(dirty8, false, false), 0.25f, n);
    Run("NaN/inf/out-of-range, [A,C] 8400", Pack(dirty8, false, true), 0.05f, n);
    Run("NaN/inf/out-of-range, [C,A] 25200", Pack(dirty5, true, false), 0.05f, n);
    Run("NaN/inf/out-of-range, [A,C] 25200", Pack(dirty5, true, true), 0.25f, n);
    Run("built-in NMS, [300,6]", PackNms(300, 5), 0.25f, n);
    printf("%s\n", gFailed ? "FAILED" : "all outputs identical");
    return gFailed ? 1 : 0;
}
