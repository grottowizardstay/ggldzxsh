#!/usr/bin/env python3
"""Open login tabs in an isolated Microsoft Edge InPrivate session."""

import argparse
import base64
import binascii
import hashlib
import hmac
import struct
import time
import os
import re
from pathlib import Path
import shutil
import sys
from urllib.parse import urlencode, urlsplit

SESSIONS_URL = 'https://github.com/settings/sessions'

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


def find_edge(override=None):
    if override:
        path = Path(override).expanduser()
        if path.is_file():
            return str(path.resolve())
        raise FileNotFoundError('The supplied Edge executable does not exist.')
    candidates = []
    if sys.platform == 'win32':
        for key in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'):
            if os.environ.get(key):
                candidates.append(Path(os.environ[key]) / 'Microsoft/Edge/Application/msedge.exe')
    elif sys.platform == 'darwin':
        candidates = [
            Path('/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge'),
            Path.home() / 'Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
        ]
    for path in candidates:
        if path.is_file():
            return str(path)
    for name in ('microsoft-edge', 'microsoft-edge-stable', 'msedge'):
        found = shutil.which(name)
        if found:
            return found
    raise FileNotFoundError('Edge was not found. Use --edge with its executable path.')


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


def totp_code(secret, timestamp=None):
    key = base64.b32decode(secret + '=' * (-len(secret) % 8))
    counter = int(time.time() if timestamp is None else timestamp) // 30
    digest = hmac.new(key, struct.pack('>Q', counter), hashlib.sha1).digest()
    offset = digest[-1] & 15
    number = struct.unpack('>I', digest[offset:offset + 4])[0] & 0x7fffffff
    return f'{number % 1000000:06d}'


def submit_github(page):
    page.evaluate("""() => {
        if (location.origin !== 'https://github.com' || location.pathname !== '/login')
            throw new Error('Unexpected login origin');
        const form = document.querySelector('#password')?.form;
        if (!form || form.method.toLowerCase() !== 'post' ||
            new URL(form.action).origin !== 'https://github.com')
            throw new Error('Unexpected login form');
        form.requestSubmit();
    }""")


def advance_login(page, secret, state):
    if state.get('sessions_opened') or page.is_closed():
        return
    url = urlsplit(page.url)
    if url.scheme != 'https' or url.netloc != 'github.com':
        return
    if url.path == '/sessions/two-factor/app' and not state.get('totp_attempted'):
        field = page.locator('input[name="app_otp"]')
        if field.count() and field.is_visible():
            state['totp_attempted'] = True
            # Generate locally rather than scraping the third-party code page.
            page.evaluate("""code => {
                if (location.origin !== 'https://github.com' ||
                    location.pathname !== '/sessions/two-factor/app')
                    throw new Error('Unexpected 2FA origin');
                const field = document.querySelector('input[name="app_otp"]');
                const form = field?.form;
                if (!form || form.method.toLowerCase() !== 'post' ||
                    new URL(form.action).origin !== 'https://github.com')
                    throw new Error('Unexpected 2FA form');
                field.value = code;
                field.dispatchEvent(new Event('input', {bubbles: true}));
                form.requestSubmit();
            }""", totp_code(secret))
            print('Submitted an authenticator code. Complete any additional verification in Edge.')
            return
    signed_in = any(cookie['name'] == 'logged_in' and cookie['value'] == 'yes'
                    for cookie in page.context.cookies(['https://github.com']))
    if signed_in and not url.path.startswith(('/login', '/sessions/')):
        if url.path != '/settings/sessions':
            page.goto(SESSIONS_URL, wait_until='domcontentloaded', timeout=30000)
        if urlsplit(page.url).path == '/settings/sessions' and urlsplit(page.url).netloc == 'github.com':
            state['sessions_opened'] = True
            page.bring_to_front()
            print('Opened GitHub Settings → Sessions. No sessions have been revoked.')


def prepare_hoplite(page, state):
    if not state.get('sessions_opened') or state.get('hoplite_prepared') or page.is_closed():
        return
    state['hoplite_prepared'] = True
    # Both tabs use the same context, so GitHub OAuth can reuse its login cookies.
    page.goto(LOGIN_URLS[1], wait_until='domcontentloaded', timeout=30000)
    url = urlsplit(page.url)
    if url.scheme != 'https' or url.netloc != 'app.hoplite.sh' or url.path != '/login':
        print('Hoplite redirected away from login. Check its tab to continue.')
        return
    button = page.get_by_role('button', name=re.compile(r'^Continue with GitHub(?: account)?$', re.I))
    button.wait_for(state='visible', timeout=15000)
    if not button.is_enabled():
        print('Hoplite’s GitHub login button is disabled. Check the page before continuing.')
        return
    page.bring_to_front()
    button.click(timeout=15000)
    print('Clicked Continue with GitHub to start Hoplite sign-in.')
    print('Review any GitHub authorization request yourself; no permissions are approved automatically.')


def launch(edge, secret, login, password):
    try:
        from playwright.sync_api import sync_playwright, Error
    except ImportError:
        print('Install the browser automation dependency: python -m pip install playwright')
        return 1
    with sync_playwright() as playwright:
        # Playwright owns and cleans up a fresh temporary browser profile.
        browser = playwright.chromium.launch(
            executable_path=edge, headless=False,
            args=['--inprivate', '--disable-extensions', '--no-first-run', '--no-default-browser-check'],
        )
        try:
            context = browser.new_context()
            github = context.new_page()
            hoplite = context.new_page()
            other_tabs = [(hoplite, LOGIN_URLS[1]),
                          (context.new_page(), 'https://2fa.fb.tools/' + secret)]
            try:
                github.goto(LOGIN_URLS[0] + '?' + urlencode({'login': login, 'return_to': '/settings/sessions'}),
                            wait_until='domcontentloaded', timeout=30000)
                fill_github(github, login, password)
                submit_github(github)
                print('GitHub login submitted. Additional challenges may require your input.')
            except (Error, ValueError):
                print('Automatic sign-in could not finish. Complete it in the GitHub tab.')
            finally:
                password = None
            for page, url in other_tabs:
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                except Error:
                    print('One of the other tabs could not finish loading. Check it in Edge.')
            try:
                github.bring_to_front()
            except Error:
                pass
            print('Keep this console open; close the new Edge windows when done.')
            state = {}
            while browser.is_connected() and context.pages:
                try:
                    try:
                        advance_login(github, secret, state)
                        prepare_hoplite(hoplite, state)
                    except (Error, ValueError):
                        if not state.get('warning_shown'):
                            print('Check the GitHub or Hoplite tab for remaining verification; the script will wait.')
                            state['warning_shown'] = True
                    context.pages[0].wait_for_timeout(250)
                except Error:
                    if not browser.is_connected() or not context.pages:
                        break
        finally:
            browser.close()
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--edge', help='Path to the Edge executable')
    args = parser.parse_args()
    try:
        edge = find_edge(args.edge)
        print('Paste log:pass:2fa-key:recovery-codes:username/profile')
        print('Input is visible in this console. Fields cannot contain colons.')
        print('The 2FA key will be sent to 2fa.fb.tools in its URL; no further confirmation.')
        print('GitHub login and authenticator verification will be submitted automatically.')
        record = input('Account data: ')
        try:
            login, password, secret = parse_record(record)
        finally:
            del record
        return launch(edge, secret, login, password)
    except (EOFError, KeyboardInterrupt):
        print('\nCancelled.')
        return 1
    except (ValueError, OSError) as exc:
        print(f'Error: {exc}')
        return 1
    except Exception:
        # Automation errors can contain input values; never echo their details.
        print('Edge automation failed. Check Edge and the Playwright installation.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
