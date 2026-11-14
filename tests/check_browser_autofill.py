"""Browser smoke check using synthetic credentials; never submits the login form."""
from test_isolated_chrome import app
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=app.find_chrome(), headless=True)
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
