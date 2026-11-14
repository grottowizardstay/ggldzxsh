import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

spec = importlib.util.spec_from_file_location('isolated_chrome', Path(__file__).parents[1] / 'scripts/isolated_chrome.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)
SECRET = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'  # Public RFC 6238 test vector.


class LauncherTests(unittest.TestCase):
    def test_parse_preserves_password(self):
        self.assertEqual(app.parse_record(f'user@example.invalid: dummy p@ss :{SECRET.lower()}:dummy:demo'),
                         ('user@example.invalid', ' dummy p@ss ', SECRET))

    def test_reject_invalid_records_without_echoing(self):
        for record in ['sensitive', 'a:b:c:d:', 'a:b:invalid-key:d:e', 'a:b:A:d:e', 'a:b:AA:d:e', 'a:b:c:d:e:f']:
            with self.subTest(record=record), self.assertRaises(ValueError) as caught:
                app.parse_record(record)
            self.assertNotIn(record, str(caught.exception))

    def test_totp_rfc_vectors(self):
        for timestamp, expected in [(59, '287082'), (1111111109, '081804'), (1111111111, '050471'), (1234567890, '005924'), (2000000000, '279037')]:
            self.assertEqual(app.totp_code(SECRET, timestamp), expected)

    def test_challenges_are_not_bypassed(self):
        page = Mock(url='https://github.com/sessions/verified-device')
        page.is_closed.return_value = False
        page.context.cookies.return_value = []
        app.advance_login(page, SECRET, {})
        page.evaluate.assert_not_called()
        page.goto.assert_not_called()

    def test_totp_is_only_attempted_once(self):
        page = Mock(url='https://github.com/sessions/two-factor/app')
        page.is_closed.return_value = False
        page.context.cookies.return_value = []
        state = {}
        app.advance_login(page, SECRET, state)
        app.advance_login(page, SECRET, state)
        page.evaluate.assert_called_once()

    def test_hoplite_waits_for_github_and_prepares_once(self):
        page = Mock(url='https://app.hoplite.sh/login')
        page.is_closed.return_value = False
        state = {}
        app.prepare_hoplite(page, state)
        page.goto.assert_not_called()
        state['sessions_opened'] = True
        app.prepare_hoplite(page, state)
        app.prepare_hoplite(page, state)
        page.goto.assert_called_once()
        page.get_by_role.return_value.focus.assert_called_once()
        page.get_by_role.return_value.click.assert_not_called()

    def test_hoplite_does_not_interact_after_external_redirect(self):
        page = Mock(url='https://example.invalid/login')
        page.is_closed.return_value = False
        app.prepare_hoplite(page, {'sessions_opened': True})
        page.get_by_role.assert_not_called()

    def test_custom_executable(self):
        with tempfile.NamedTemporaryFile() as file:
            self.assertEqual(app.find_chrome(file.name), str(Path(file.name).resolve()))
        with self.assertRaises(FileNotFoundError):
            app.find_chrome('/nonexistent/chrome')

    def test_visible_input_without_confirmation(self):
        record = f'user@example.invalid:dummy-password:{SECRET}:dummy:demo'
        with patch.object(app.sys, 'argv', ['script']), patch.object(app, 'find_chrome', return_value='/chrome'), patch('builtins.input', return_value=record) as prompt, patch.object(app, 'launch', return_value=0) as launch:
            self.assertEqual(app.main(), 0)
            prompt.assert_called_once_with('Account data: ')
            launch.assert_called_once_with('/chrome', SECRET, 'user@example.invalid', 'dummy-password')

    def test_foreign_origin_does_not_receive_credentials(self):
        for url in ['http://github.com/login', 'https://github.com.evil.invalid/login', 'https://evil.invalid/login']:
            page = Mock(url=url)
            with self.assertRaises(ValueError):
                app.fill_github(page, 'dummy', 'dummy-password')
            page.evaluate.assert_not_called()

    def test_automation_errors_do_not_print_password(self):
        with patch.object(app.sys, 'argv', ['script']), patch.object(app, 'find_chrome', return_value='/chrome'), patch('builtins.input', return_value=f'a:dummy-password:{SECRET}:d:e'), patch.object(app, 'launch', side_effect=RuntimeError('dummy-password')), patch('builtins.print') as output:
            self.assertEqual(app.main(), 1)
            self.assertNotIn('dummy-password', str(output.call_args_list))


if __name__ == '__main__':
    unittest.main()
