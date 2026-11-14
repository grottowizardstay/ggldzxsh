from pathlib import Path
import unittest
from unittest.mock import patch

import isolated_edge as script
from textual.widgets import Button, Static


class TerminalTests(unittest.IsolatedAsyncioTestCase):
    async def test_demo_layout_clicks_and_keys(self):
        app = script.build_terminal_app('octocat-demo', demo=True)
        async with app.run_test(size=(88, 34)) as pilot:
            with patch.object(app, 'copy_to_clipboard') as copy:
                for key, expected in [('number', '4242424242424242'), ('expiry', '12/2028'),
                                      ('cvv', '123'), ('all', '4242424242424242|12|2028|123')]:
                    await pilot.click('#copy-' + key)
                    copy.assert_called_with(expected)
                await pilot.press('1')
                copy.assert_called_with('4242424242424242')
            with patch.object(app._driver, 'write') as write:
                app.action_copy_field('cvv')
                write.assert_called_with('\x1b]52;c;MTIz\a')
            Path('/tmp/verify').mkdir(exist_ok=True)
            app.save_screenshot('terminal-console.svg', '/tmp/verify')
            await pilot.resize_terminal(60, 34)
            await pilot.pause()
            self.assertTrue(app.query_one('#copy-number').region.right <= 60)
            app.save_screenshot('terminal-console-narrow.svg', '/tmp/verify')

    async def test_waiting_and_error(self):
        app = script.build_terminal_app('[red]literal-account')
        async with app.run_test(size=(88, 34)) as pilot:
            self.assertTrue(app.query_one('#copy-number', Button).disabled)
            self.assertIn('[red]literal-account', str(app.query_one('#account', Static).render()))
            with patch.object(app, 'copy_to_clipboard') as copy:
                await pilot.press('1')
                copy.assert_not_called()
            app.show_card(None)
            self.assertTrue(app.query_one('#copy-all', Button).disabled)
            app.show_card(dict(number='4242424242424242', month='12', year='2028', cvv='123'))
            self.assertFalse(app.query_one('#copy-all', Button).disabled)


if __name__ == '__main__':
    unittest.main()
