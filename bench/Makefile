# Cross-builds the benchmarks with mingw-w64. On Windows with MSVC:
#   cl /std:c++17 /O2 /EHsc /I stubs bench.cpp d3d11.lib d3dcompiler.lib dxgi.lib
#   cl /std:c++17 /O2 /EHsc /I stubs hid_bench.cpp
CXX := x86_64-w64-mingw32-g++-posix
CXXFLAGS := -std=c++17 -O2 -Wall -Wno-unknown-pragmas -static -I stubs
STUBS := $(wildcard stubs/support/*.hpp)

all: bench.exe hid_bench.exe
bench.exe: bench.cpp ../FrameProcessor.hpp baseline/FrameProcessor.hpp $(STUBS)
	$(CXX) $(CXXFLAGS) -o $@ bench.cpp -ld3d11 -ld3dcompiler_47 -ldxgi
hid_bench.exe: hid_bench.cpp ../HidInput.hpp baseline/HidInput.hpp $(STUBS)
	$(CXX) $(CXXFLAGS) -o $@ hid_bench.cpp -lhid -lsetupapi
clean:
	rm -f bench.exe hid_bench.exe
