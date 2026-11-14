# Windows executable

`AccountConsole.exe` is a 64-bit Windows console application. It bundles Python,
Textual, and Playwright; Microsoft Edge must already be installed.

- Extract the entire archive with 7-Zip (LZMA-compressed ZIP); keep the `_internal` folder beside the executable.
- Keep `card.txt` beside the executable, not inside a temporary extraction folder.
- Start the executable from Windows Terminal to keep errors visible.
- Run `AccountConsole.exe --demo` to preview test data without reading cards or signing in.
- Click a field or use 1–4 to request clipboard copying; this needs terminal OSC 52 support.
- The card entry is removed after the GitHub button click, not confirmed sign-in.
- No payment is submitted. The executable is unsigned.

To rebuild on Windows, install 64-bit Python 3.12 and run `build_windows.bat`.
The output is `dist\AccountConsole\AccountConsole.exe`. The build explicitly includes only the
script and installed dependencies, never account records or card files.
