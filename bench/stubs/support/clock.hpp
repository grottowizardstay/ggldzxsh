#pragma once
// Benchmark stand-in for the application's clock.
#include <windows.h>

inline double PerfNowMs() noexcept {
    static const double factor = [] { LARGE_INTEGER f{}; QueryPerformanceFrequency(&f); return 1000.0 / double(f.QuadPart); }();
    LARGE_INTEGER t{}; QueryPerformanceCounter(&t);
    return double(t.QuadPart) * factor;
}
