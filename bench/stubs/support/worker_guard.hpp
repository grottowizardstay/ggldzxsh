#pragma once
// Benchmark stand-in for the application's worker wrapper.
#include <exception>

namespace vision {
template<class Body, class OnError, class OnExit>
void GuardWorker(Body&& body, OnError&& onError, OnExit&& onExit) noexcept {
    try { body(); }
    catch (const std::exception& e) { onError(e.what()); }
    catch (...) { onError("unknown"); }
    onExit();
}
}
