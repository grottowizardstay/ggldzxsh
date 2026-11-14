#pragma once
// Benchmark stand-in for the application's detector state helper.
namespace vision {
inline bool DetectorIsLoading(bool exited, bool ready, bool failed) noexcept { return !exited && !ready && !failed; }
}
