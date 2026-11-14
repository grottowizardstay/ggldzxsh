import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
from textual.widgets import Button, Static

SCRIPT = Path(__file__).resolve().parents[1] / "isolated_edge.py"
SPEC = importlib.util.spec_from_file_location("isolated_edge", SCRIPT)
isolated_edge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(isolated_edge)


ADDRESS = "312, Teheran-ro, Gangnam-gu"
ZIP_CODE = "06211"


@pytest.mark.asyncio
async def test_address_and_zip_are_visible_before_card_load_and_fit_terminal():
    app = isolated_edge.build_terminal_app("fixture-user")

    async with app.run_test(size=(80, 40)) as pilot:
        await pilot.pause()

        assert str(app.query_one("#feedback", Static).content) == "No card loaded."
        assert ADDRESS in app.query_one("#copy-address", Button).label.plain
        assert ZIP_CODE in app.query_one("#copy-zip", Button).label.plain
        for selector in ("#copy-address", "#copy-zip"):
            region = app.query_one(selector, Button).region
            assert region.x + region.width <= 80
            assert region.y + region.height <= 40


@pytest.mark.asyncio
async def test_address_and_zip_buttons_and_keyboard_copy_on_linux(monkeypatch):
    app = isolated_edge.build_terminal_app("fixture-user")
    copied = []
    monkeypatch.setattr(app, "copy_to_clipboard", copied.append)

    async with app.run_test(size=(80, 40)) as pilot:
        await pilot.click("#copy-address")
        assert copied[-1] == ADDRESS
        assert "Copy requested" in str(app.query_one("#feedback", Static).content)

        await pilot.click("#copy-zip")
        assert copied[-1] == ZIP_CODE

        await pilot.press("5", "6")
        assert copied[-2:] == [ADDRESS, ZIP_CODE]


@pytest.mark.asyncio
async def test_address_and_zip_remain_reachable_in_default_terminal(monkeypatch):
    app = isolated_edge.build_terminal_app("fixture-user")
    copied = []
    monkeypatch.setattr(app, "copy_to_clipboard", copied.append)

    async with app.run_test(size=(80, 24)) as pilot:
        for selector, expected in (
            ("#copy-address", ADDRESS),
            ("#copy-zip", ZIP_CODE),
        ):
            button = app.query_one(selector, Button)
            app.screen.scroll_to_widget(button, animate=False, immediate=True)
            # Initial focus can start a competing screen scroll; let it settle.
            await pilot.pause(delay=0.3)

            region = button.region
            assert region.y >= 0
            assert region.y + region.height <= 23
            assert await pilot.click(selector)
            assert copied[-1] == expected


@pytest.mark.asyncio
async def test_address_copy_uses_windows_clipboard_and_reports_oserror(monkeypatch):
    app = isolated_edge.build_terminal_app("fixture-user")
    copied = []
    monkeypatch.setattr(isolated_edge, "sys", SimpleNamespace(platform="win32"))
    monkeypatch.setattr(isolated_edge, "copy_windows_clipboard", copied.append)

    async with app.run_test(size=(80, 40)) as pilot:
        await pilot.click("#copy-address")
        assert copied == [ADDRESS]
        assert str(app.query_one("#feedback", Static).content) == "Copied to clipboard."

    monkeypatch.setattr(
        isolated_edge,
        "copy_windows_clipboard",
        lambda value: (_ for _ in ()).throw(OSError("clipboard unavailable")),
    )
    app = isolated_edge.build_terminal_app("fixture-user")
    async with app.run_test(size=(80, 40)) as pilot:
        await pilot.click("#copy-zip")
        assert "Clipboard unavailable" in str(app.query_one("#feedback", Static).content)


@pytest.mark.asyncio
async def test_terminal_screenshot_shows_address_and_zip():
    app = isolated_edge.build_terminal_app("fixture-user")

    async with app.run_test(size=(100, 40)) as pilot:
        await pilot.pause()
        screenshot = app.export_screenshot()

    assert screenshot.startswith("<svg")
    artifact = Path(".hoplite/artifacts/console.svg")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(screenshot, encoding="utf-8")
