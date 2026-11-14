# Cross-builds the benchmarks with mingw-w64. With MSVC, compile the same sources with
# /std:c++17 /O2 /EHsc /I stubs (plus /I .. and the defines below for the detector benchmark).
CXX := x86_64-w64-mingw32-g++-posix
CXXFLAGS := -std=c++17 -O2 -Wall -Wno-unknown-pragmas -static -I stubs
STUBS := $(wildcard stubs/support/*.hpp)
DETECTOR_SRC := detector_bench.cpp ../ObjectDetector.cpp baseline/detector/ObjectDetector.cpp
DETECTOR_DEPS := $(DETECTOR_SRC) ../ObjectDetector.hpp baseline/detector/ObjectDetector.hpp ../FrameProcessor.hpp $(STUBS)

all: bench.exe hid_bench.exe detector_bench.exe detector_bench_1class.exe
bench.exe: bench.cpp ../FrameProcessor.hpp baseline/FrameProcessor.hpp $(STUBS)
	$(CXX) $(CXXFLAGS) -o $@ bench.cpp -ld3d11 -ld3dcompiler_47 -ldxgi
hid_bench.exe: hid_bench.cpp ../HidInput.hpp baseline/HidInput.hpp $(STUBS)
	$(CXX) $(CXXFLAGS) -o $@ hid_bench.cpp -lhid -lsetupapi

# The baseline detector is compiled as BaselineObjectDetector so both versions link into one program.
# The class count and the single decoded class are compile-time constants in the application, so
# there is one build for an 80-class model and one for a single-class model.
define detector_build
$(1): $(DETECTOR_DEPS)
	$(CXX) $(CXXFLAGS) -I .. $(2) -c -o $(1).new.o ../ObjectDetector.cpp
	$(CXX) $(CXXFLAGS) -I .. $(2) -DObjectDetector=BaselineObjectDetector -c -o $(1).base.o baseline/detector/ObjectDetector.cpp
	$(CXX) $(CXXFLAGS) -I .. $(2) -o $(1) detector_bench.cpp $(1).new.o $(1).base.o -ld3d11 -ld3dcompiler_47 -ldxgi
	rm -f $(1).new.o $(1).base.o
endef
$(eval $(call detector_build,detector_bench.exe,-DBENCH_NUM_CLASSES=80 -DBENCH_DECODE_CLASS=-1))
$(eval $(call detector_build,detector_bench_1class.exe,-DBENCH_NUM_CLASSES=1 -DBENCH_DECODE_CLASS=0))

clean:
	rm -f *.exe *.o
