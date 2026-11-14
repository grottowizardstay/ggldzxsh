# Benchmarks

Each benchmark runs the original header from `baseline/` and the current one from the repository
root side by side. `stubs/support/` stands in for the application headers they include.

```
make                 # mingw-w64 cross-build; see the Makefile for the MSVC commands
bench.exe [frames]   # FrameProcessor, default 300 frames per row
hid_bench.exe        # HidInput
```

Run them on the target machine: the reference numbers below come from Wine on 2 shared vCPUs with
no GPU and no HID board, so they show direction only.

## FrameProcessor (`bench.exe`)

Reports output equivalence (baseline vs. new, and vs. a CPU bilinear reference), `Init` time,
CPU cost of `Submit`, submit-to-CPU latency per tensor format and wait strategy, and the frames
delivered by a paced capture loop that makes one non-blocking fetch per tick.

Wine 9.0 + DXVK 2.5.3 on llvmpipe, 200 frames per row, range over three runs. Run-to-run noise is
large; differences under about 1 ms are not significant.

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

## HidInput (`hid_bench.exe`)

No device is opened. `stubs/support/overlapped_io.hpp` replaces the write with a simulated device
that accepts one report per 1 ms frame and records what it received, and the benchmark attaches it
to both versions directly. Connecting and enumeration are therefore not exercised.

Range over three runs:

| | baseline | new |
|---|---|---|
| code overhead per `SendCommand`, instant device | 215 ns | 210 ns |
| code overhead per `QueueMove`, sender already awake | n/a | 26 ns |
| caller blocked, 5 px move | 0.94 ms | 0.04–0.06 ms queued |
| caller blocked, 1000 px move | 7.9 ms | 0.06–0.08 ms queued |
| 1000 px move complete at the device | 7.9 ms | 8.1 ms queued |
| 4000 one-pixel moves wanted in 1 s | loop takes 4.0 s, 4000 reports | loop takes 1.0 s, about 1000 reports, all 4000 px delivered |
| two threads, 500 moves each | 0–7 dropped | 0 dropped |
| caller blocked by a 25 ms click | 26.9 ms | 0.07 ms queued |
| click hold seen by the device | 26 ms | 28 ms |

The blocking calls behave as before. A queued call costs tens of microseconds when it has to wake
the sender thread, most of it the wake-up itself under Wine.
