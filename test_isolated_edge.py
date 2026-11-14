import tempfile
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
import isolated_edge as script


class ConfirmationTests(unittest.TestCase):
    def page(self, button=False, field=False):
        page = MagicMock()
        page.get_by_role.return_value.count.return_value = int(button)
        page.get_by_role.return_value.first.is_visible.return_value = button
        page.locator.return_value.count.return_value = int(field)
        page.locator.return_value.nth.return_value.is_visible.return_value = field
        return page

    def test_optional_challenge(self):
        self.assertFalse(script.confirm_second_factor(self.page(), '', {}))

    def test_click_and_wait_for_delayed_field(self):
        state = {}
        page = self.page(button=True)
        self.assertTrue(script.confirm_second_factor(page, '', state))
        page.get_by_role.return_value.first.click.assert_called_once()
        self.assertTrue(script.confirm_second_factor(self.page(), '', state))

    @patch('isolated_edge.time.time', return_value=60)
    def test_no_reuse_of_first_code(self, clock):
        page = self.page(field=True)
        state = {'confirmation_opened': True, 'first_totp_counter': 2}
        self.assertTrue(script.confirm_second_factor(page, '', state))
        page.evaluate.assert_not_called()

    @patch('isolated_edge.time.time', return_value=90)
    def test_submit_once_and_wait_for_field_to_disappear(self, clock):
        page = self.page(button=True, field=True)
        state = {'confirmation_opened': True, 'first_totp_counter': 2}
        secret = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'
        self.assertTrue(script.confirm_second_factor(page, secret, state))
        self.assertTrue(script.confirm_second_factor(page, secret, state))
        page.evaluate.assert_called_once()
        self.assertFalse(script.confirm_second_factor(self.page(), secret, state))

    def test_totp_known_vector(self):
        self.assertEqual(script.totp_code('GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ', 59), '287082')

    def test_hoplite_waits(self):
        page = MagicMock()
        script.prepare_hoplite(page, {'confirmation_opened': True})
        page.goto.assert_not_called()


class CardTests(unittest.TestCase):
    def test_consume_one_preserves_remaining_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'card.txt'
            first = b'4242424242424242|12|2028|123'
            second = b'5555555555554444|01|2029|456'
            path.write_bytes(b'\r\n' + first + b'\r\n' + second + b'\r\n')
            self.assertEqual(script.take_card(path)['number'], '4242424242424242')
            self.assertEqual(path.read_bytes(), b'\r\n' + second + b'\r\n')
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_bad_and_empty_input_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'card.txt'
            for data in (b'', b'bad entry', b'4242424242424242|13|2028|123'):
                path.write_bytes(data)
                with self.assertRaises(ValueError):
                    script.take_card(path)
                self.assertEqual(path.read_bytes(), data)

    def test_failed_replace_preserves_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'card.txt'
            data = b'4242424242424242|12|2028|123'
            path.write_bytes(data)
            with patch('isolated_edge.os.replace', side_effect=OSError):
                with self.assertRaises(OSError):
                    script.take_card(path)
            self.assertEqual(path.read_bytes(), data)
            self.assertEqual(list(Path(directory).iterdir()), [path])

    @patch('isolated_edge.take_card', return_value={'number': 'test'})
    def test_load_only_after_successful_click_and_once(self, take):
        page = MagicMock()
        page.is_closed.return_value = False
        page.url = script.LOGIN_URLS[1]
        state = {'sessions_opened': True}
        page.get_by_role.return_value.click.side_effect = lambda **kw: take.assert_not_called()
        script.prepare_hoplite(page, state)
        script.prepare_hoplite(page, state)
        take.assert_called_once_with()
        self.assertEqual(state['card'], {'number': 'test'})

    @patch('isolated_edge.take_card')
    def test_failed_click_does_not_consume(self, take):
        page = MagicMock()
        page.is_closed.return_value = False
        page.url = script.LOGIN_URLS[1]
        page.get_by_role.return_value.click.side_effect = RuntimeError
        with self.assertRaises(RuntimeError):
            script.prepare_hoplite(page, {'sessions_opened': True})
        take.assert_not_called()


if __name__ == '__main__':
    unittest.main()
