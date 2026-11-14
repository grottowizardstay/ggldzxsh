// Compares the original HidInput (bench/baseline) with the current one against a simulated device
// (see stubs/support/overlapped_io.hpp), since no RawHID board is attached where this runs.
#include "support/platform.hpp"
#include <setupapi.h>
// mingw-w64's hidsdi.h omits the C linkage the MSVC header declares itself.
extern "C" {
#include <hidsdi.h>
}
#include <algorithm>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cwchar>
#include <cwctype>
#include <mutex>
#include <string>
#include <thread>
#include <vector>
#include "support/overlapped_io.hpp"
#include "support/worker_guard.hpp"
#include "support/diagnostics.hpp"

// Both versions keep the device handle private; the benchmark attaches the fake device directly.
// Every header they include is already included above.
#define private public
namespace baseline {
#include "baseline/HidInput.hpp"
}
#include "../HidInput.hpp"
#undef private

using vision::gFake;
using vision::FakeNowUs;

template<class H> static void Attach(H& hid) {
    std::lock_guard<std::mutex> io(hid.mIoMx);
    hid.mReportLength = 65; hid.mPacket.assign(65, 0);
    hid.mDevice = CreateEventW(nullptr, TRUE, FALSE, nullptr);
    hid.mConnected = true;
}

static double Median(std::vector<double> v) { std::sort(v.begin(), v.end()); return v.empty() ? 0 : v[v.size() / 2]; }
static void SpinUntil(long long us) { while (FakeNowUs() < us) YieldProcessor(); }
static bool gFailed = false;
static void Check(bool ok, const char* what) { if (!ok) { gFailed = true; printf("[FAIL] %s\n", what); } }

int main() {
    baseline::HidInput base; HidInput cur;
    Attach(base); Attach(cur);

    // 1. Per-call overhead of the code itself, with the device answering instantly.
    {
        gFake.periodUs = 0;
        const int n = 2000000;
        auto time = [&](auto&& fn) { const auto t0 = FakeNowUs(); for (int i = 0; i < n; ++i) fn(); return double(FakeNowUs() - t0) * 1000.0 / n; };
        double b = 1e9, c = 1e9, q = 1e9;
        for (int rep = 0; rep < 5; ++rep) {
            b = std::min(b, time([&] { base.SendCommand(0, 1, 1); }));
            c = std::min(c, time([&] { cur.SendCommand(0, 1, 1); }));
            q = std::min(q, time([&] { cur.QueueMove(1, 1); }));
            cur.Flush(5000);
        }
        printf("code overhead per call, instant device (best of 5): baseline SendCommand %.1f ns | new SendCommand %.1f ns | new QueueMove %.1f ns\n\n", b, c, q);
    }

    gFake.periodUs = 1000;
    printf("simulated device: one report per 1 ms frame\n");

    // 2. How long the caller is held up, and when the device has the whole move.
    for (int dist : { 5, 1000 }) {
        std::vector<double> bc, cc, qc, bd, qd;
        for (int i = 0; i < 50; ++i) {
            gFake.Reset(); auto t0 = FakeNowUs(); base.MoveRelative(dist, -dist); bc.push_back((FakeNowUs() - t0) / 1000.0); bd.push_back(bc.back());
            Check(gFake.sumX == dist && gFake.sumY == -dist, "baseline move total");
            gFake.Reset(); t0 = FakeNowUs(); cur.MoveRelative(dist, -dist); cc.push_back((FakeNowUs() - t0) / 1000.0);
            Check(gFake.sumX == dist && gFake.sumY == -dist, "new blocking move total");
            gFake.Reset(); t0 = FakeNowUs(); cur.QueueMove(dist, -dist); qc.push_back((FakeNowUs() - t0) / 1000.0);
            Check(cur.Flush(5000), "flush"); qd.push_back((FakeNowUs() - t0) / 1000.0);
            Check(gFake.sumX == dist && gFake.sumY == -dist, "queued move total");
        }
        printf("move of %4d px, median ms: caller blocked: baseline %.3f | new MoveRelative %.3f | new QueueMove %.4f; at device: baseline %.3f | queued %.3f\n",
            dist, Median(bc), Median(cc), Median(qc), Median(bd), Median(qd));
    }

    // 3. A producer that wants to send 4000 small moves in one second, faster than the device takes reports.
    {
        const int calls = 4000; const long long spacingUs = 250;
        auto run = [&](auto&& send, auto&& finish) {
            gFake.Reset();
            const long long t0 = FakeNowUs(); int ok = 0;
            for (int i = 0; i < calls; ++i) { SpinUntil(t0 + i * spacingUs); if (send()) ++ok; }
            const double loopMs = (FakeNowUs() - t0) / 1000.0;
            finish();
            printf("loop took %7.1f ms (wanted %.0f), %d calls accepted, %lld reports, %lld of %d px delivered\n",
                loopMs, calls * spacingUs / 1000.0, ok, gFake.reports.load(), gFake.sumX.load(), calls);
        };
        printf("\n4 kHz producer, 1 px per call\n  baseline MoveRelative: "); run([&] { return base.MoveRelative(1, 0); }, [] {});
        printf("  new QueueMove:         "); run([&] { return cur.QueueMove(1, 0); }, [&] { Check(cur.Flush(5000), "flush"); });
        Check(gFake.sumX == calls, "queued producer total");
    }

    // 4. Two threads sending at once.
    {
        const int perThread = 500;
        auto run = [&](auto&& send) {
            gFake.Reset(); std::atomic<int> rejected{0};
            auto worker = [&] { for (int i = 0; i < perThread; ++i) { if (!send()) ++rejected; Sleep(1); } };
            std::thread a(worker), b(worker); a.join(); b.join();
            return rejected.load();
        };
        const int rb = run([&] { return base.MoveRelative(1, 0); }); const long long db = gFake.sumX;
        const int rq = run([&] { return cur.QueueMove(1, 0); }); Check(cur.Flush(5000), "flush"); const long long dq = gFake.sumX;
        printf("\ntwo threads, %d moves each: baseline dropped %d (%lld of %d px delivered) | new QueueMove dropped %d (%lld of %d px delivered)\n",
            perThread, rb, db, 2 * perThread, rq, dq, 2 * perThread);
        Check(rq == 0 && dq == 2 * perThread, "queued two-thread total");
    }

    // 5. Click with a 25 ms hold.
    {
        std::vector<double> bc, qc, bh, qh;
        for (int i = 0; i < 20; ++i) {
            gFake.Reset(); auto t0 = FakeNowUs(); base.Click(25); bc.push_back((FakeNowUs() - t0) / 1000.0); bh.push_back(gFake.holdUs / 1000.0);
            gFake.Reset(); t0 = FakeNowUs(); cur.QueueClick(25); qc.push_back((FakeNowUs() - t0) / 1000.0);
            Check(cur.Flush(5000), "flush"); qh.push_back(gFake.holdUs / 1000.0);
            Check(gFake.presses == 1 && gFake.buttons == 0, "queued click press and release");
        }
        gFake.Reset(); cur.QueueClick(5); cur.QueueClick(5); cur.QueueMove(300, 0); Check(cur.Flush(5000), "flush");
        Check(gFake.presses == 2 && gFake.buttons == 0 && gFake.sumX == 300, "two queued clicks with motion");
        printf("\nclick, 25 ms hold, median ms: caller blocked: baseline %.2f | new QueueClick %.4f; hold seen by device: baseline %.2f | queued %.2f\n",
            Median(bc), Median(qc), Median(bh), Median(qh));
    }

    printf("\n%s\n", gFailed ? "FAILED" : "all checks passed");
    return gFailed ? 1 : 0;
}
