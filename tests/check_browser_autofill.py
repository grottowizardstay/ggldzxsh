"""Browser smoke check using synthetic credentials; never submits the login form."""
from test_isolated_edge import app
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=app.find_edge(), headless=True, args=['--inprivate'])
    context = browser.new_context()
    page = context.new_page()
    page.goto('https://github.com/login', wait_until='domcontentloaded')
    app.fill_github(page, 'launcher-test@example.invalid', 'synthetic-test-password')
    assert page.locator('#login_field').input_value() == 'launcher-test@example.invalid'
    assert page.locator('#password').input_value() == 'synthetic-test-password'
    assert page.url == 'https://github.com/login'
    assert 'synthetic-test-password' not in page.url
    context.add_cookies([{'name': 'isolation_test', 'value': 'test', 'url': 'https://github.com'}])
    other = browser.new_context()
    assert other.cookies() == []
    other.close()
    browser.close()
print('PASS: real GitHub form filled without submission; separate context has no inherited cookies.')

# All requests in this flow are intercepted; no credentials are sent to GitHub.
from urllib.parse import parse_qs
from unittest.mock import patch
from test_isolated_edge import SECRET

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=app.find_edge(), headless=True, args=['--inprivate'])
    context = browser.new_context()
    submissions = []
    def route_request(route):
        path = route.request.url.split('github.com', 1)[-1]
        if path == '/login':
            body = '<form method="post" action="/session"><input id="login_field" name="login"><input id="password" name="password" type="password"><button>Sign in</button></form>'
        elif path == '/session':
            submissions.append(parse_qs(route.request.post_data))
            route.fulfill(status=200, content_type='text/html', body='<script>location.replace("/sessions/two-factor/app")</script>')
            return
        elif path == '/sessions/two-factor/app':
            body = '<form method="post" action="/sessions/two-factor"><input name="app_otp"><button>Verify</button></form>'
        elif path == '/sessions/two-factor':
            submissions.append(parse_qs(route.request.post_data))
            context.add_cookies([{'name': 'logged_in', 'value': 'yes', 'url': 'https://github.com'}])
            route.fulfill(status=200, content_type='text/html', body='<script>location.replace("/")</script>')
            return
        else:
            body = '<h1>Sessions</h1>' if path == '/settings/sessions' else '<h1>Home</h1>'
        route.fulfill(status=200, content_type='text/html', body=body)
    context.route('**/*', route_request)
    page = context.new_page()
    page.goto('https://github.com/login')
    app.fill_github(page, 'synthetic-user', 'synthetic-password')
    app.submit_github(page)
    page.wait_for_url('**/sessions/two-factor/app')
    page.locator('input[name="app_otp"]').wait_for(state='visible')
    state = {}
    with patch.object(app.time, 'time', return_value=59):
        app.advance_login(page, SECRET, state)
    page.wait_for_url('https://github.com/')
    app.advance_login(page, SECRET, state)
    assert state == {'totp_attempted': True, 'sessions_opened': True}
    assert page.url == app.SESSIONS_URL
    assert submissions == [{'login': ['synthetic-user'], 'password': ['synthetic-password']}, {'app_otp': ['287082']}]
    app.advance_login(page, SECRET, state)
    assert len(submissions) == 2
    browser.close()
print('PASS: intercepted login, 2FA submission and Sessions navigation; no live account login attempted.')
