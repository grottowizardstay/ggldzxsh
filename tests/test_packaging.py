from types import SimpleNamespace

import pytest

from test_isolated_edge import isolated_edge


def test_frozen_card_path_is_beside_executable(tmp_path, monkeypatch):
    install = tmp_path / 'install'
    install.mkdir()
    work = tmp_path / 'work'
    work.mkdir()
    monkeypatch.chdir(work)
    monkeypatch.setattr(isolated_edge, 'sys', SimpleNamespace(
        frozen=True, executable=str(install / 'isolated_edge.exe')))
    card_file = install / 'card.txt'
    card_file.write_text('4242424242424242|12|2028|123\n')

    assert isolated_edge.take_card()['number'] == '4242424242424242'
    assert card_file.read_text() == ''
    assert not (install / 'card.txt.lock').exists()
    assert not (work / 'card.txt').exists()


@pytest.mark.asyncio
async def test_loading_card_preserves_address_and_original_full_entry():
    app = isolated_edge.build_terminal_app('test-user', demo=True)
    async with app.run_test(size=(80, 40)):
        assert app.values['address'] == '312, Teheran-ro, Gangnam-gu'
        assert app.values['zip'] == '06211'
        assert app.values['all'] == '4242424242424242|12|2028|123'
