#pragma once
// Benchmark stand-in for the application's overlapped I/O helpers. Instead of a HID device, Write
// feeds a simulated one that accepts a single report per USB frame and records what it received.
#include <windows.h>
#include <atomic>
#include <cstdint>

namespace vision {

struct IoResult { bool ok = false; DWORD bytes = 0; DWORD error = 0; };

inline long long FakeNowUs() noexcept {
    static const double factor = [] { LARGE_INTEGER f{}; QueryPerformanceFrequency(&f); return 1000000.0 / double(f.QuadPart); }();
    LARGE_INTEGER t{}; QueryPerformanceCounter(&t);
    return static_cast<long long>(double(t.QuadPart) * factor);
}

struct FakeDevice {
    std::atomic<long long> periodUs{1000};   // frame length; 0 completes writes immediately
    std::atomic<long long> reports{0}, sumX{0}, sumY{0}, presses{0}, pressUs{0}, holdUs{0};
    std::atomic<int> buttons{0};
    void Reset() noexcept { reports = 0; sumX = 0; sumY = 0; presses = 0; pressUs = 0; holdUs = 0; buttons = 0; }
};
inline FakeDevice gFake;

inline IoResult Write(HANDLE, const uint8_t* data, DWORD size, DWORD, std::atomic<bool>*) noexcept {
    const long long period = gFake.periodUs.load(std::memory_order_relaxed);
    if (period > 0) {
        // The report leaves in the next frame, as on a full-speed interrupt OUT endpoint.
        const long long due = (FakeNowUs() / period + 1) * period;
        while (FakeNowUs() < due) YieldProcessor();
    }
    gFake.reports.fetch_add(1, std::memory_order_relaxed);
    gFake.sumX.fetch_add(int8_t(data[2]), std::memory_order_relaxed);
    gFake.sumY.fetch_add(int8_t(data[3]), std::memory_order_relaxed);
    const int now = data[1] & 1, before = gFake.buttons.exchange(now, std::memory_order_relaxed);
    if (now && !before) { gFake.presses.fetch_add(1, std::memory_order_relaxed); gFake.pressUs = FakeNowUs(); }
    if (!now && before) gFake.holdUs = FakeNowUs() - gFake.pressUs.load();
    return { true, size, 0 };
}

inline IoResult Read(HANDLE, uint8_t*, DWORD, DWORD, std::atomic<bool>*) noexcept { return { false, 0, ERROR_TIMEOUT }; }

class Handle {
public:
    explicit Handle(HANDLE value) noexcept : mValue(value) {}
    ~Handle() { if (mValue != INVALID_HANDLE_VALUE) CloseHandle(mValue); }
    Handle(const Handle&) = delete;
    Handle& operator=(const Handle&) = delete;
    HANDLE Release() noexcept { HANDLE v = mValue; mValue = INVALID_HANDLE_VALUE; return v; }
private:
    HANDLE mValue;
};

}
