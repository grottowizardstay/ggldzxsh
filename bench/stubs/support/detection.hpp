#pragma once
// Benchmark stand-in for the application's detection types.
#include <cstdint>

struct Detection { float x = 0, y = 0, w = 0, h = 0, score = 0; int cls = 0; };

struct DetectionTiming {
    std::uint64_t frameId = 0;
    double capturedMs = 0, submittedMs = 0, completedMs = 0, inferenceMs = 0, decodeMs = 0;
    double workerStartedMs = 0, presentedMs = 0, acquiredMs = 0;
    std::uint32_t accumulatedFrames = 0;
    float roiX = 0, roiY = 0, roiWidth = 0, roiHeight = 0, letterboxRatio = 1, padX = 0, padY = 0;
    int netSide = 0;
};
