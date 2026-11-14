# FrameProcessor benchmark

`bench.exe` runs the original header (`baseline/FrameProcessor.hpp`) and the current one
(`../FrameProcessor.hpp`) against the same D3D11 device and reports:

- output equivalence (baseline vs. new, and vs. a CPU bilinear reference),
- `Init` time with runtime compilation and with precompiled bytecode,
- CPU cost of `Submit`,
- submit-to-CPU latency per tensor format and wait strategy,
- frames delivered by a paced capture loop that makes one non-blocking fetch per tick.

## Running

```
make                 # mingw-w64 cross-build; see the Makefile for the MSVC command
bench.exe [frames]   # default 300 frames per row
```

Run it on the target GPU: the numbers below are from a software rasterizer and only show direction.

## Reference results

Wine 9.0 + DXVK 2.5.3 on llvmpipe (2 shared vCPUs, no GPU), 200 frames per row, range over three runs.
Run-to-run noise on this machine is large; differences under about 1 ms are not significant.

| net 640 | baseline | new |
|---|---|---|
| float32 output | reference | bit-identical |
| `Init` | 5.6–6.4 ms | 6.9–7.8 ms compiling, 1.1–1.2 ms with bytecode |
| `Submit` CPU cost (median) | 26–27 µs | 25–28 µs |
| latency, float32, 1 ms poll (median) | 7.4–7.6 ms | 7.2–7.6 ms |
| latency, float32, event wait | n/a | 3.8–7.0 ms |
| latency, float16, event wait | n/a | 3.0–4.9 ms |
| latency, unorm8, event wait | n/a | 2.7–3.8 ms |
| CPU fetch (map + copy), median | 0.24–0.28 ms float32 | 0.10–0.14 ms float16, 0.03–0.05 ms unorm8 |
| 16 ms tick, fetch right after submit | 0 of 200 frames | 196–197 of 200 |
| 4 ms tick (GPU overloaded), fetch before submit | 0–1 of 200 | 56–93 float32, 142–157 unorm8 |

At net 320, where this device keeps up, both versions deliver 177–196 of 200 frames on the 4 ms tick,
and the baseline still delivers 0 of 200 when the fetch follows the submit.
