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
