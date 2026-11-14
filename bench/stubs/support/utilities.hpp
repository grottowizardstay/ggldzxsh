#pragma once
// Benchmark stand-in for the application's string and file helpers.
#include <string>

inline std::string WideToUtf8(const std::wstring& s) { return std::string(s.begin(), s.end()); }
inline bool ReadTextFileUtf8(const std::wstring&, std::string&) { return false; }
