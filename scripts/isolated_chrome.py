#!/usr/bin/env python3
"""Open login tabs in a disposable Chrome profile. Requires Python 3.10+."""

import argparse
import base64
import binascii
import os
from pathlib import Path
import shutil
import sys
from urllib.parse import urlencode, urlsplit

LOGIN_URLS = ('https://github.com/login', 'https://app.hoplite.sh/login')


def parse_record(record):
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
    return fields[0].strip(), fields[1], secret


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


def fill_github(page, login, password):
    if urlsplit(page.url).scheme != 'https' or urlsplit(page.url).netloc != 'github.com':
        raise ValueError('GitHub redirected to another site; credentials were not entered.')
    page.locator('#password').wait_for(state='visible', timeout=15000)
    # Check the origin again inside the same operation that fills the fields.
    page.evaluate("""({login, password}) => {
        if (location.origin !== 'https://github.com')
            throw new Error('Unexpected login origin');
        const user = document.querySelector('#login_field');
        const pass = document.querySelector('#password');
        if (!user || !pass || pass.type !== 'password' || !pass.form ||
            user.form !== pass.form || pass.form.method.toLowerCase() !== 'post' ||
            new URL(pass.form.action).origin !== 'https://github.com')
            throw new Error('Unexpected login form');
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        for (const [field, value] of [[user, login], [pass, password]]) {
            setter.call(field, value);
            field.dispatchEvent(new Event('input', {bubbles: true}));
            field.dispatchEvent(new Event('change', {bubbles: true}));
        }
    }""", {'login': login, 'password': password})


def launch(chrome, secret, login, password):
    try:
        from playwright.sync_api import sync_playwright, Error
    except ImportError:
        print('Install the browser automation dependency: python -m pip install playwright')
        return 1
    with sync_playwright() as playwright:
        # Playwright owns and cleans up a fresh temporary browser profile.
        browser = playwright.chromium.launch(
            executable_path=chrome, headless=False,
            args=['--disable-extensions', '--no-first-run', '--no-default-browser-check'],
        )
        try:
            context = browser.new_context()
            github = context.new_page()
            other_tabs = [(context.new_page(), LOGIN_URLS[1]),
                          (context.new_page(), 'https://2fa.fb.tools/' + secret)]
            try:
                github.goto(LOGIN_URLS[0] + '?' + urlencode({'login': login}),
                            wait_until='domcontentloaded', timeout=30000)
                fill_github(github, login, password)
                print('GitHub username and password filled. Click Sign in when ready.')
            except (Error, ValueError):
                print('GitHub could not be filled. Check the page and enter credentials manually.')
            finally:
                password = None
            for page, url in other_tabs:
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                except Error:
                    print('One of the other tabs could not finish loading. Check it in Chrome.')
            try:
                github.bring_to_front()
            except Error:
                pass
            print('Keep this console open; close the new Chrome windows when done.')
            while browser.is_connected() and context.pages:
                try:
                    context.pages[0].wait_for_timeout(250)
                except Error:
                    if not browser.is_connected() or not context.pages:
                        break
        finally:
            browser.close()
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chrome', help='Path to the Chrome executable')
    args = parser.parse_args()
    try:
        chrome = find_chrome(args.chrome)
        print('Paste log:pass:2fa-key:recovery-codes:username/profile')
        print('Input is visible in this console. Fields cannot contain colons.')
        print('The 2FA key will be sent to 2fa.fb.tools in its URL; no further confirmation.')
        print('GitHub credentials will be filled automatically, but not submitted.')
        record = input('Account data: ')
        try:
            login, password, secret = parse_record(record)
        finally:
            del record
        return launch(chrome, secret, login, password)
    except (EOFError, KeyboardInterrupt):
        print('\nCancelled.')
        return 1
    except (ValueError, OSError) as exc:
        print(f'Error: {exc}')
        return 1
    except Exception:
        # Automation errors can contain input values; never echo their details.
        print('Chrome automation failed. Check Chrome and the Playwright installation.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
