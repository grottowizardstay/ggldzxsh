#!/usr/bin/env python3
"""Open login tabs in a disposable Chrome profile. Requires Python 3.10+."""

import argparse
import base64
import binascii
import getpass
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import warnings

LOGIN_URLS = ('https://github.com/login', 'https://app.hoplite.sh/login')


def parse_secret(record):
    fields = record.strip().split(':')
    if len(fields) != 5 or any(not field.strip() for field in fields):
        raise ValueError('Enter exactly five nonempty colon-separated fields.')
    secret = fields[2].strip().upper()
    if any(char not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567' for char in secret):
        raise ValueError('The 2FA key must be an unpadded Base32 secret.')
    try:
        decoded = base64.b32decode(secret + '=' * (-len(secret) % 8))
    except (binascii.Error, ValueError):
        raise ValueError('The 2FA key is not valid Base32.') from None
    if len(decoded) < 10:
        raise ValueError('The 2FA key must contain at least 80 bits.')
    return secret


def find_chrome(override=None):
    if override:
        path = Path(override).expanduser()
        if path.is_file():
            return str(path.resolve())
        raise FileNotFoundError('The supplied Chrome executable does not exist.')
    candidates = []
    if sys.platform == 'win32':
        for key in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'):
            if os.environ.get(key):
                candidates.append(Path(os.environ[key]) / 'Google/Chrome/Application/chrome.exe')
    elif sys.platform == 'darwin':
        candidates = [
            Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
            Path.home() / 'Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        ]
    for path in candidates:
        if path.is_file():
            return str(path)
    for name in ('google-chrome', 'google-chrome-stable', 'chrome', 'chromium', 'chromium-browser'):
        found = shutil.which(name)
        if found:
            return found
    raise FileNotFoundError('Chrome was not found. Use --chrome with its executable path.')


def build_command(chrome, profile, secret=None):
    command = [
        chrome, f'--user-data-dir={profile}', '--incognito', '--new-window',
        '--no-first-run', '--no-default-browser-check', '--disable-extensions',
        *LOGIN_URLS,
    ]
    if secret:
        command.append('https://2fa.fb.tools/' + secret)
    return command


def remove_profile(profile):
    for attempt in range(10):
        try:
            shutil.rmtree(profile)
            return True
        except FileNotFoundError:
            return True
        except OSError:
            time.sleep(0.3)
    return False


def launch(chrome, secret):
    profile = tempfile.mkdtemp(prefix='isolated-chrome-')
    try:
        # Do not expose the secret URL through Chrome's diagnostic output.
        process = subprocess.Popen(
            build_command(chrome, profile, secret),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        print('Chrome launched. Keep this console open and close all new Chrome windows when done.')
        while True:
            try:
                code = process.wait()
                break
            except KeyboardInterrupt:
                print('\nClose the isolated Chrome windows to finish and remove their temporary profile.')
        if code:
            print(f'Chrome exited with status {code}. Check your Chrome installation and desktop session.')
        return code
    finally:
        if not remove_profile(profile):
            print(f'Temporary profile cleanup was blocked. Close Chrome, then delete: {profile}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chrome', help='Path to the Chrome executable')
    args = parser.parse_args()
    try:
        chrome = find_chrome(args.chrome)
        print('Paste log:pass:2fa-key:recovery-codes:username/profile')
        print('Input is hidden. Fields cannot contain colons. No automatic login or credential saving.')
        with warnings.catch_warnings():
            warnings.simplefilter('error', getpass.GetPassWarning)
            record = getpass.getpass('Account data: ')
        try:
            secret = parse_secret(record)
        finally:
            del record
        print('\nWARNING: The 2FA tab sends your reusable secret to 2fa.fb.tools.')
        print('That site can generate your future codes. The URL may also appear in local process listings.')
        print('Use a trusted local authenticator instead if you do not want to disclose it.')
        approved = input('Type SEND to open that tab, or press Enter to open only the login tabs: ')
        if approved.strip() != 'SEND':
            secret = None
        return launch(chrome, secret)
    except (EOFError, KeyboardInterrupt):
        print('\nCancelled.')
        return 1
    except getpass.GetPassWarning:
        print('Hidden input is unavailable. Run this script in a normal terminal; no input was read.')
        return 1
    except (ValueError, OSError) as exc:
        print(f'Error: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
