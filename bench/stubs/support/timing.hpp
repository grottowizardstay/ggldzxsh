#pragma once
// Benchmark stand-in for the application's latency statistics.
struct LatencyWindow {
    double last = 0; unsigned count = 0;
    void Add(double ms) noexcept { last = ms; ++count; }
};
