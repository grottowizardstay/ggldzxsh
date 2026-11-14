# Isolated Edge console

Windows x64 console application. Microsoft Edge must already be installed;
Python is not required to run the packaged executable.

Run `isolated_edge.exe --demo` from a terminal to preview sample data without
opening a browser or reading `card.txt`. Run without `--demo` for the original
sign-in flow. Use only accounts and payment details you are authorized to use.

Click the address or ZIP button to copy `312, Teheran-ro, Gangnam-gu` or `06211`.
Keyboard shortcuts **5** and **6** do the same. Existing shortcuts **1–4** and
the pipe-separated card-only “Copy full entry” format are unchanged.
Windows builds copy directly to the Windows clipboard. Other platforms require
terminal OSC 52 support. Clear your clipboard after copying sensitive data.

Keep `card.txt` beside the executable in a writable folder. The existing format
is `number|MM|YYYY|CVV`, one entry per line. The original behavior is preserved:
loading a card **removes that entry from the file**. The card file and credentials
are not bundled. This application does not submit payments.

## Build on Windows

Install 64-bit Python 3.13, then run `build_windows.bat`. The result is
`dist\isolated_edge.exe`, a single-file console executable. It is unsigned.

## Source checks

Install `requirements.txt`, `pytest`, and `pytest-asyncio`, then run
`python -m pytest`. Run `python isolated_edge.py --demo` for the sample console.