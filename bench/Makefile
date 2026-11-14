# Cross-builds the benchmark with mingw-w64. On Windows with MSVC:
#   cl /std:c++17 /O2 /EHsc /I stubs bench.cpp d3d11.lib d3dcompiler.lib dxgi.lib
CXX := x86_64-w64-mingw32-g++-posix
bench.exe: bench.cpp ../FrameProcessor.hpp baseline/FrameProcessor.hpp
	$(CXX) -std=c++17 -O2 -Wall -static -I stubs -o $@ bench.cpp -ld3d11 -ld3dcompiler_47 -ldxgi
clean:
	rm -f bench.exe
