#pragma once
// Benchmark stand-in for the application's model output contract.
#include <string>

struct ModelOutputContract {
    enum class Format { Auto, Yolo8, Yolo5, NmsXYXY };
    Format format = Format::Auto;
    bool anchorsFirst = false, normalized = false, verifiedNms = false;
    static bool ParseText(const std::string&, ModelOutputContract&, std::string&) { return false; }
    std::string Describe() const { return "auto"; }
};
