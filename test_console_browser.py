from pathlib import Path
import unittest

import isolated_edge as script

try:
    from playwright.sync_api import sync_playwright, expect
except ImportError:
    sync_playwright = None


@unittest.skipIf(sync_playwright is None, 'Playwright is not installed')
class ConsoleBrowserTests(unittest.TestCase):
    def test_console_and_clipboard(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = script.open_account_console(browser, 'octocat-demo')
                self.assertTrue(page.get_by_role('button', name='Copy card number').is_disabled())
                page.context.grant_permissions(['clipboard-read', 'clipboard-write'], origin=script.CONSOLE_URL)
                card = dict(number='4242424242424242', month='12', year='2028', cvv='123')
                state = dict(console_page=page, login='octocat-demo', card=card)
                script.update_account_console(state)
                self.assertEqual(page.locator('#number').inner_text(), '4242 4242 4242 4242')
                for label, value in [
                    ('Copy card number', card['number']),
                    ('Copy expiration date', '12/2028'),
                    ('Copy CVV', '123'),
                    ('Copy full entry', '4242424242424242|12|2028|123'),
                ]:
                    page.get_by_role('button', name=label).click()
                    expect(page.locator('#feedback')).to_have_text('Copied to clipboard.')
                    self.assertEqual(page.evaluate('navigator.clipboard.readText()'), value)
                    page.evaluate("document.querySelector('#feedback').textContent = ''")
                page.get_by_role('button', name='Copy card number').focus()
                page.keyboard.press('Enter')
                expect(page.locator('#feedback')).to_have_text('Copied to clipboard.')
                self.assertEqual(page.evaluate('navigator.clipboard.readText()'), card['number'])
                Path('/tmp/verify').mkdir(exist_ok=True)
                page.set_viewport_size({'width': 1100, 'height': 1000})
                page.screenshot(path='/tmp/verify/account-console-desktop.png', full_page=True)
                page.set_viewport_size({'width': 390, 'height': 844})
                self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                page.screenshot(path='/tmp/verify/account-console-mobile.png', full_page=True)
                state['login'] = '<img src=x onerror=alert(1)>'
                script.update_account_console(state)
                self.assertEqual(page.locator('#account').inner_text(), state['login'])
                self.assertEqual(page.locator('#account img').count(), 0)
                page.evaluate("Object.defineProperty(navigator.clipboard, 'writeText', {value: () => Promise.reject(new Error())})")
                page.get_by_role('button', name='Copy CVV').click()
                expect(page.locator('#feedback')).to_contain_text('Clipboard unavailable')
                page.close()
                script.update_account_console(state)
            finally:
                browser.close()


if __name__ == '__main__':
    unittest.main()
