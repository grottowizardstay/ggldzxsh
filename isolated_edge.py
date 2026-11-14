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
import tempfile
from urllib.parse import urlencode, urlsplit

SESSIONS_URL = 'https://github.com/settings/sessions'

LOGIN_URLS = ('https://github.com/login', 'https://app.hoplite.sh/login')


CONSOLE_URL = 'https://account-console.invalid/'
CONSOLE_HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Account console</title><style>
:root{color-scheme:dark;font-family:Inter,Segoe UI,sans-serif;color:#e7edf7;background:#0b1018}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(ellipse at 80% 0,#18312b 0,transparent 50%);padding:56px 24px}
main{max-width:820px;margin:auto}.top{display:flex;justify-content:space-between;align-items:center;gap:16px;margin-bottom:38px}.brand{font-size:14px;font-weight:650;letter-spacing:.04em}.mark{color:#8ee6bd;margin-right:10px}.local{font:11px monospace;letter-spacing:.08em;color:#9cb0c0;border:1px solid #31433d;padding:8px 12px;border-radius:30px}
.eyebrow{color:#8ee6bd;font:11px monospace;letter-spacing:.15em}h1{font-size:36px;letter-spacing:-1.3px;margin:12px 0}p{color:#9baabc;font-size:14px;line-height:1.6}.profile{display:flex;align-items:center;gap:24px;margin:30px 0;padding:24px;border:1px solid #2a3544;border-radius:18px;background:#121b27}
.avatar{margin:0;color:#8ee6bd;background:#1c302d;border:1px solid #345248;border-radius:14px;padding:16px;font:16px/1.2 monospace;flex-shrink:0}.account{font-size:21px;font-weight:600;overflow-wrap:anywhere}.profile>div{min-width:0}.profile p{margin:7px 0 0;font-size:12px}.section{display:flex;justify-content:space-between;align-items:center;margin:34px 0 16px;gap:12px}h2{font-size:16px;margin:0}.tag{font:11px monospace;color:#a9b8cb}
.card{border:1px solid #354454;border-radius:20px;padding:28px;background:linear-gradient(125deg,#1d2c3b,#15221f);box-shadow:0 18px 50px #0003}.cardhead{display:flex;justify-content:space-between;align-items:center;margin-bottom:26px}.chip{color:#98c9b3;border:1px solid #789789;border-radius:7px;width:36px;text-align:center;font:23px monospace}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.number{grid-column:1/-1}
button{font:inherit;color:inherit;cursor:pointer}.field{display:flex;align-items:center;justify-content:space-between;gap:12px;text-align:left;border:1px solid #3b4b56;background:#0b141b66;border-radius:12px;padding:16px 18px;min-width:0}.field:hover:not(:disabled){border-color:#8ee6bd;background:#1a3531}.field:focus-visible,.all:focus-visible{outline:2px solid #8ee6bd;outline-offset:4px}.field:disabled{cursor:default;opacity:.5}.label{display:block;color:#aebbc8;font:10px monospace;letter-spacing:.12em;margin-bottom:8px}.value{font:19px monospace;letter-spacing:.04em}.number .value{font-size:25px}.copy{color:#93b9a9;font-size:12px;white-space:nowrap}.bottom{display:flex;justify-content:space-between;align-items:center;gap:14px;margin-top:24px}.all{background:#a3ebc6;border:0;color:#10271d;font-size:13px;font-weight:650;border-radius:9px;padding:12px 16px}.all:disabled{opacity:.4;cursor:default}#feedback{font-size:12px;color:#a3ebc6;min-height:20px;margin:0}.note{margin-top:22px;font-size:12px;color:#9baabc}footer{border-top:1px solid #28313d;margin-top:38px;padding-top:18px;color:#8e9eaf;font:11px/1.7 monospace}
@media(max-width:560px){body{padding:28px 16px}h1{font-size:30px}.profile{gap:16px;padding:18px}.avatar{font-size:12px;padding:12px}.card{padding:18px}.grid{grid-template-columns:1fr}.number{grid-column:auto}.number .value{font-size:16px}.bottom{align-items:flex-start;flex-direction:column}.local{font-size:9px}.copy{font-size:11px}}
</style></head><body><main>
<header class="top"><div class="brand"><span class="mark">&gt;_</span> ACCOUNT CONSOLE</div><span class="local">● LOCAL SESSION</span></header>
<div class="eyebrow">YOUR SESSION, AT A GLANCE</div><h1>A little space for your account.</h1><p>GitHub identity above. Your selected card, one click away.</p>
<section class="profile" aria-label="GitHub account"><pre class="avatar" aria-label="Character cat avatar"> /\_/\
( o.o )
 &gt; ^ &lt;</pre><div><span class="label">GITHUB ACCOUNT</span><div class="account" id="account"></div><p id="status" role="status">Waiting for Continue with GitHub.</p></div></section>
<div class="section"><h2>Selected card</h2><span class="tag">CLICK A FIELD TO COPY</span></div>
<section class="card" aria-label="Selected card details"><div class="cardhead"><span class="eyebrow">PAYMENT DETAILS</span><span class="chip" aria-hidden="true">▦</span></div>
<div class="grid"><button class="field number" data-copy="number" disabled aria-label="Copy card number"><span><span class="label">CARD NUMBER</span><span class="value" id="number">•••• •••• •••• ••••</span></span><span class="copy">Copy ↗</span></button>
<button class="field" data-copy="expiry" disabled aria-label="Copy expiration date"><span><span class="label">EXPIRATION</span><span class="value" id="expiry">MM / YYYY</span></span><span class="copy">Copy ↗</span></button>
<button class="field" data-copy="cvv" disabled aria-label="Copy CVV"><span><span class="label">CVV</span><span class="value" id="cvv">•••</span></span><span class="copy">Copy ↗</span></button></div>
<div class="bottom"><p id="feedback" role="status" aria-live="polite">No card loaded yet.</p><button class="all" data-copy="all" disabled>Copy full entry ↗</button></div></section>
<p class="note">Details stay in this browser session. Copying puts them on your system clipboard; clear it when finished.</p>
<footer>No payment is submitted here. The GitHub button click does not confirm sign-in.<br>Closing the script clears the session, not your clipboard.</footer>
</main><script>
let values = {};
window.renderAccount = ({login, card, error}) => {
 document.getElementById('account').textContent = login;
 document.getElementById('status').textContent = card ? 'GitHub sign-in started · one card loaded' : error ? 'Card unavailable · check card.txt and its permissions' : 'Waiting for Continue with GitHub.';
 if (!card) return;
 values = {number:card.number, expiry:`${card.month}/${card.year}`, cvv:card.cvv, all:`${card.number}|${card.month}|${card.year}|${card.cvv}`};
 document.getElementById('number').textContent = card.number.replace(/(.{4})(?=.)/g,'$1 ');
 document.getElementById('expiry').textContent = `${card.month} / ${card.year}`;
 document.getElementById('cvv').textContent = card.cvv;
 document.querySelectorAll('[data-copy]').forEach(button => button.disabled = false);
 document.getElementById('feedback').textContent = 'Entry removed from card.txt.';
};
document.querySelectorAll('[data-copy]').forEach(button => button.addEventListener('click', async () => {
 try {
  await navigator.clipboard.writeText(values[button.dataset.copy]);
  document.getElementById('feedback').textContent = 'Copied to clipboard.';
 } catch {
  document.getElementById('feedback').textContent = 'Clipboard unavailable. Select and copy the text manually.';
 }
}));
</script></body></html>'''


def open_account_console(browser, login):
    context = browser.new_context()
    # This isolated origin is fulfilled in memory; it never contacts a server.
    context.route('**/*', lambda route: route.fulfill(
        status=200, content_type='text/html', body=CONSOLE_HTML,
        headers={'Content-Security-Policy': "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; form-action 'none'; base-uri 'none'"},
    ) if route.request.url == CONSOLE_URL else route.abort())
    context.grant_permissions(['clipboard-write'], origin=CONSOLE_URL)
    page = context.new_page()
    page.goto(CONSOLE_URL)
    page.evaluate('data => window.renderAccount(data)', {'login': login})
    return page


def update_account_console(state):
    page = state.get('console_page')
    if page is not None and not page.is_closed() and page.url == CONSOLE_URL:
        page.evaluate('data => window.renderAccount(data)', {
            'login': state['login'], 'card': state.get('card'),
            'error': not bool(state.get('card')),
        })
        page.bring_to_front()


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
    print('Submitted the second authenticator code; waiting for GitHub confirmation.')
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
            print('Submitted an authenticator code. Complete any additional verification in Edge.')
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
            print('Opened GitHub Settings → Sessions. No sessions have been revoked.')


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
    try:
        state['card'] = take_card()
        print('Loaded one card into memory and removed its entry from card.txt. No payment submitted.')
    except (OSError, ValueError):
        print('Card loading failed; no card was loaded. Check card.txt and its permissions.')
    update_account_console(state)
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
            console_page = open_account_console(browser, login)
            context = browser.new_context()
            github = context.new_page()
            hoplite = context.new_page()
            other_tabs = [(hoplite, LOGIN_URLS[1])]
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
            state = {'console_page': console_page, 'login': login}
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
        print('Authenticator codes are generated locally; the key is not sent to another site.')
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
