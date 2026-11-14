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
    def test_parse(self):
        self.assertEqual(app.parse_record(f'user@example.invalid:dummy:{SECRET.lower()}:dummy:demo'), ('user@example.invalid', SECRET))

    def test_reject_invalid_records_without_echoing(self):
        for record in ['sensitive', 'a:b:c:d:', 'a:b:invalid-key:d:e', 'a:b:A:d:e', 'a:b:AA:d:e', 'a:b:c:d:e:f']:
            with self.subTest(record=record), self.assertRaises(ValueError) as caught:
                app.parse_record(record)
            self.assertNotIn(record, str(caught.exception))

    def test_command(self):
        command = app.build_command('/chrome', '/temporary profile', SECRET)
        self.assertIn('--user-data-dir=/temporary profile', command)
        self.assertIn('--incognito', command)
        self.assertIn('--disable-extensions', command)
        self.assertEqual(command[-3:], [*app.LOGIN_URLS, 'https://2fa.fb.tools/' + SECRET])

    def test_no_disclosure_without_secret(self):
        self.assertEqual(app.build_command('/chrome', '/temp')[-2:], list(app.LOGIN_URLS))

    def test_custom_executable(self):
        with tempfile.NamedTemporaryFile() as file:
            self.assertEqual(app.find_chrome(file.name), str(Path(file.name).resolve()))
        with self.assertRaises(FileNotFoundError):
            app.find_chrome('/nonexistent/chrome')

    def test_launch_cleans_profile(self):
        profiles = []
        def spawn(command, **kwargs):
            profile = command[1].split('=', 1)[1]
            self.assertTrue(Path(profile).is_dir())
            profiles.append(profile)
            return Mock(wait=Mock(return_value=0))
        with patch.object(app.subprocess, 'Popen', side_effect=spawn):
            self.assertEqual(app.launch('/chrome', None), 0)
            self.assertEqual(app.launch('/chrome', None), 0)
        self.assertNotEqual(*profiles)
        self.assertTrue(all(not Path(p).exists() for p in profiles))

    def test_failed_start_cleans_profile(self):
        with tempfile.TemporaryDirectory() as parent:
            profile = Path(parent) / 'profile'
            profile.mkdir()
            with patch.object(app.tempfile, 'mkdtemp', return_value=str(profile)), patch.object(app.subprocess, 'Popen', side_effect=OSError('Cannot start')):
                with self.assertRaises(OSError):
                    app.launch('/chrome', None)
            self.assertFalse(profile.exists())

    def test_visible_input_opens_tabs_without_confirmation(self):
        record = f'user@example.invalid:dummy-password:{SECRET}:dummy:demo'
        with patch.object(app.sys, 'argv', ['script']), patch.object(app, 'find_chrome', return_value='/chrome'), patch('builtins.input', return_value=record) as prompt, patch.object(app, 'launch', return_value=0) as launch:
            self.assertEqual(app.main(), 0)
            prompt.assert_called_once_with('Account data: ')
            launch.assert_called_once_with('/chrome', SECRET, 'user@example.invalid')

    def test_login_url_encodes_username_only(self):
        from urllib.parse import urlparse, parse_qs
        login = 'example+test&name@example.invalid'
        command = app.build_command('/chrome', '/temp', SECRET, login)
        url = urlparse(command[-3])
        self.assertEqual(url.netloc, 'github.com')
        self.assertEqual(parse_qs(url.query), {'login': [login]})
        self.assertNotIn('password', url.query)


if __name__ == '__main__':
    unittest.main()
