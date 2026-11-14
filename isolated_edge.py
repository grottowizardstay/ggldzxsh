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
import threading
import tempfile
from urllib.parse import urlencode, urlsplit

SESSIONS_URL = 'https://github.com/settings/sessions'

LOGIN_URLS = ('https://github.com/login', 'https://app.hoplite.sh/login')


def build_terminal_app(login, demo=False):
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal, Vertical
    from textual.widgets import Button, Footer, Static
    from rich.text import Text

    class AccountConsole(App):
        TITLE = 'GitHub account console'
        CSS = '''
        Screen { background: #0b1018; color: #e7edf7; }
        #panel { width: 76; max-width: 100%; height: auto; margin: 1 2; padding: 1 2;
                 border: round #44675e; background: #121b27; }
        #brand { color: #8ee6bd; text-style: bold; margin-bottom: 1; }
        #profile { height: auto; margin-bottom: 0; }
        #avatar { width: 13; height: 3; color: #8ee6bd; }
        #identity { width: 1fr; height: auto; }
        #account { text-style: bold; margin-bottom: 1; }
        #status { color: #aebccc; }
        #heading { color: #8ee6bd; margin-top: 1; margin-bottom: 1; }
        Button { width: 100%; height: 3; margin-bottom: 0; background: #20332f;
                 color: #e7edf7; border: round #44675e; content-align: left middle; text-align: left; }
        Button:hover { background: #304e44; }
        Button:focus { border: round #a3ebc6; text-style: bold; }
        #copy-all { color: #a3ebc6; }
        #feedback { margin-top: 1; color: #a3ebc6; min-height: 2; }
        #note { color: #9baabc; margin-top: 1; }
        Footer { background: #18222f; }
        '''
        BINDINGS = [('1', 'copy_field("number")', 'Number'),
                    ('2', 'copy_field("expiry")', 'Expiry'),
                    ('3', 'copy_field("cvv")', 'CVV'),
                    ('4', 'copy_field("all")', 'Full entry'),
                    ('q', 'quit', 'Quit')]

        def __init__(self):
            super().__init__()
            self.values = {}
            self.start_browser = None

        def compose(self) -> ComposeResult:
            with Container(id='panel'):
                yield Static('>_  GITHUB ACCOUNT CONSOLE', id='brand')
                with Horizontal(id='profile'):
                    yield Static(' /\\_/\\\n( o.o )\n > ^ <', id='avatar')
                    with Vertical(id='identity'):
                        yield Static(login, id='account', markup=False)
                        yield Static('Waiting for GitHub sign-in…', id='status', markup=False)
                yield Static('SELECTED CARD  /  click a field or press 1–4', id='heading')
                yield Button('1  Number     —', id='copy-number', disabled=True)
                yield Button('2  Expiry     —', id='copy-expiry', disabled=True)
                yield Button('3  CVV        —', id='copy-cvv', disabled=True)
                yield Button('4  Copy full entry', id='copy-all', disabled=True)
                yield Static('No card loaded.', id='feedback', markup=False)
                yield Static('Local display only · no payment submitted.\n'
                             'Copy needs terminal OSC 52 support. Clear your clipboard when finished.',
                             id='note', markup=False)
            yield Footer()

        def on_mount(self):
            if demo:
                self.show_card(dict(number='4242424242424242', month='12', year='2028', cvv='123'))
                self.show_status('DEMO · sample account and test card only')
            elif self.start_browser:
                self.start_browser()

        def show_status(self, message):
            self.query_one('#status', Static).update(message)

        def show_card(self, card):
            if not card:
                self.query_one('#feedback', Static).update('Card unavailable. Check card.txt and its permissions.')
                return
            self.values = dict(number=card['number'], expiry=f"{card['month']}/{card['year']}",
                               cvv=card['cvv'], all='|'.join(card[key] for key in ('number', 'month', 'year', 'cvv')))
            for key, label in (('number', '1  Number'), ('expiry', '2  Expiry'), ('cvv', '3  CVV')):
                button = self.query_one('#copy-' + key, Button)
                button.label = Text(f'{label:<13}{self.values[key]}')
                button.disabled = False
            self.query_one('#copy-all', Button).disabled = False
            self.query_one('#feedback', Static).update('Test data only.' if demo else 'Loaded in memory · entry removed from card.txt.')

        def on_button_pressed(self, event: Button.Pressed):
            self.action_copy_field(event.button.id.removeprefix('copy-'))

        def action_copy_field(self, key):
            if key not in self.values:
                return
            self.copy_to_clipboard(self.values[key])
            self.query_one('#feedback', Static).update('Copy requested. If unsupported, use terminal text selection.')

    return AccountConsole()


def run_terminal(edge, secret, login, password):
    app = build_terminal_app(login)
    stop = threading.Event()
    result = [0]

    def update(method, value):
        try:
            app.call_from_thread(method, value)
        except RuntimeError:
            pass

    def worker():
        try:
            result[0] = launch(edge, secret, login, password,
                               log=lambda message: update(app.show_status, message),
                               on_card=lambda card: update(app.show_card, card), stop=stop)
        except Exception:
            result[0] = 1
            update(app.show_status, 'Edge automation failed. Check Edge and the Playwright installation.')

    thread = threading.Thread(target=worker, name='edge-session')
    app.start_browser = thread.start
    try:
        app.run()
    finally:
        stop.set()
        if thread.ident is not None:
            thread.join()
    return result[0]


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


def confirm_second_factor(page, secret, state):
    button = page.get_by_role('button', name=re.compile(r'^Verify 2FA now$', re.I))
    if not state.get('confirmation_opened') and button.count() and button.first.is_visible():
        button.first.click(timeout=15000)
        state['confirmation_opened'] = True
        return True
    if not state.get('confirmation_opened'):
        return False
    field = page.locator('input[name="app_otp"], input[name="otp"], input[autocomplete="one-time-code"]')
    visible = any(field.nth(i).is_visible() for i in range(field.count()))
    if not visible:
        # Do not mistake a delayed challenge for completed verification.
        return not state.get('confirmation_submitted')
    if state.get('confirmation_submitted'):
        return True
    counter = int(time.time()) // 30
    if counter == state.get('first_totp_counter'):
        return True
    page.evaluate("""code => {
        if (location.origin !== 'https://github.com')
            throw new Error('Unexpected confirmation origin');
        const fields = [...document.querySelectorAll(
            'input[name="app_otp"], input[name="otp"], input[autocomplete="one-time-code"]')];
        const field = fields.find(el => el.getClientRects().length && !el.disabled);
        const form = field?.form;
        if (!form || form.method.toLowerCase() !== 'post' ||
            new URL(form.action).origin !== 'https://github.com')
            throw new Error('Unexpected confirmation form');
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        setter.call(field, code);
        field.dispatchEvent(new Event('input', {bubbles: true}));
        field.dispatchEvent(new Event('change', {bubbles: true}));
        form.requestSubmit();
    }""", totp_code(secret, counter * 30))
    state['confirmation_submitted'] = True
    state.get('log', print)('Submitted the second authenticator code; waiting for GitHub confirmation.')
    return True


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
            state['first_totp_counter'] = int(time.time()) // 30
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
            }""", totp_code(secret, state['first_totp_counter'] * 30))
            state.get('log', print)('Submitted an authenticator code. Complete any additional verification in Edge.')
            return
    if confirm_second_factor(page, secret, state):
        return
    signed_in = any(cookie['name'] == 'logged_in' and cookie['value'] == 'yes'
                    for cookie in page.context.cookies(['https://github.com']))
    if signed_in and not url.path.startswith(('/login', '/sessions/')):
        if url.path != '/settings/sessions':
            page.goto(SESSIONS_URL, wait_until='domcontentloaded', timeout=30000)
        if urlsplit(page.url).path == '/settings/sessions' and urlsplit(page.url).netloc == 'github.com':
            if confirm_second_factor(page, secret, state):
                return
            state['sessions_opened'] = True
            page.bring_to_front()
            state.get('log', print)('Opened GitHub Settings → Sessions. No sessions have been revoked.')


def take_card(path=None):
    path = Path(path) if path is not None else Path(__file__).resolve().with_name('card.txt')
    lock = path.with_name(path.name + '.lock')
    # Serialize consumption across script instances; fail closed on a stale lock.
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    temporary = None
    try:
        lines = path.read_bytes().splitlines(keepends=True)
        index = next((i for i, line in enumerate(lines) if line.strip()), None)
        if index is None:
            raise ValueError('card.txt has no entries.')
        try:
            entry = lines[index].decode('ascii').strip()
        except UnicodeDecodeError:
            raise ValueError('Invalid card entry format; card.txt was not changed.') from None
        if not re.fullmatch(r'[0-9]{12,19}\|(?:0[1-9]|1[0-2])\|[0-9]{4}\|[0-9]{3,4}', entry):
            raise ValueError('Invalid card entry format; card.txt was not changed.')
        number, month, year, cvv = entry.split('|')
        card = dict(number=number, month=month, year=year, cvv=cvv)
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.card-', delete=False) as output:
            temporary = Path(output.name)
            output.write(b''.join(lines[:index] + lines[index + 1:]))
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        return card
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        lock.unlink(missing_ok=True)


def prepare_hoplite(page, state):
    if not state.get('sessions_opened') or state.get('hoplite_prepared') or page.is_closed():
        return
    state['hoplite_prepared'] = True
    # Both tabs use the same context, so GitHub OAuth can reuse its login cookies.
    page.goto(LOGIN_URLS[1], wait_until='domcontentloaded', timeout=30000)
    url = urlsplit(page.url)
    if url.scheme != 'https' or url.netloc != 'app.hoplite.sh' or url.path != '/login':
        state.get('log', print)('Hoplite redirected away from login. Check its tab to continue.')
        return
    button = page.get_by_role('button', name=re.compile(r'^Continue with GitHub(?: account)?$', re.I))
    button.wait_for(state='visible', timeout=15000)
    if not button.is_enabled():
        state.get('log', print)('Hoplite’s GitHub login button is disabled. Check the page before continuing.')
        return
    page.bring_to_front()
    button.click(timeout=15000)
    state.get('log', print)('Clicked Continue with GitHub to start Hoplite sign-in.')
    try:
        state['card'] = take_card()
        state.get('log', print)('Loaded one card into memory and removed its entry from card.txt. No payment submitted.')
    except (OSError, ValueError):
        state.get('log', print)('Card loading failed; no card was loaded. Check card.txt and its permissions.')
    if state.get('on_card'):
        state['on_card'](state.get('card'))
    state.get('log', print)('Review any GitHub authorization request yourself; no permissions are approved automatically.')


def launch(edge, secret, login, password, log=print, on_card=None, stop=None):
    try:
        from playwright.sync_api import sync_playwright, Error
    except ImportError:
        log('Install the browser automation dependency: python -m pip install playwright')
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
            other_tabs = [(hoplite, LOGIN_URLS[1])]
            try:
                github.goto(LOGIN_URLS[0] + '?' + urlencode({'login': login, 'return_to': '/settings/sessions'}),
                            wait_until='domcontentloaded', timeout=30000)
                fill_github(github, login, password)
                submit_github(github)
                log('GitHub login submitted. Additional challenges may require your input.')
            except (Error, ValueError):
                log('Automatic sign-in could not finish. Complete it in the GitHub tab.')
            finally:
                password = None
            for page, url in other_tabs:
                try:
                    page.goto(url, wait_until='domcontentloaded', timeout=30000)
                except Error:
                    log('One of the other tabs could not finish loading. Check it in Edge.')
            try:
                github.bring_to_front()
            except Error:
                pass
            log('Keep this console open; close the new Edge windows when done.')
            state = {'log': log, 'on_card': on_card}
            while browser.is_connected() and context.pages and not (stop and stop.is_set()):
                try:
                    try:
                        advance_login(github, secret, state)
                        prepare_hoplite(hoplite, state)
                    except (Error, ValueError):
                        if not state.get('warning_shown'):
                            log('Check the GitHub or Hoplite tab for remaining verification; the script will wait.')
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
    parser.add_argument('--demo', action='store_true', help='Preview the terminal console with test data; no browser or card file')
    args = parser.parse_args()
    try:
        try:
            import textual
        except ImportError:
            print('Install dependencies: python -m pip install playwright textual')
            return 1
        if args.demo:
            build_terminal_app('octocat-demo', demo=True).run()
            return 0
        edge = find_edge(args.edge)
        print('Paste log:pass:2fa-key:recovery-codes:username/profile')
        print('Input is visible in this console. Fields cannot contain colons.')
        print('Authenticator codes are generated locally; the key is not sent to another site.')
        print('GitHub login and authenticator verification will be submitted automatically.')
        record = input('Account data: ')
        try:
            login, password, secret = parse_record(record)
        finally:
            del record
        return run_terminal(edge, secret, login, password)
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
