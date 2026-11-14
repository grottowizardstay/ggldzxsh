import unittest
from unittest.mock import MagicMock, patch
import isolated_edge as script


class ConfirmationTests(unittest.TestCase):
    def page(self, button=False, field=False):
        page = MagicMock()
        page.get_by_role.return_value.count.return_value = int(button)
        page.get_by_role.return_value.first.is_visible.return_value = button
        page.locator.return_value.count.return_value = int(field)
        page.locator.return_value.nth.return_value.is_visible.return_value = field
        return page

    def test_optional_challenge(self):
        self.assertFalse(script.confirm_second_factor(self.page(), '', {}))

    def test_click_and_wait_for_delayed_field(self):
        state = {}
        page = self.page(button=True)
        self.assertTrue(script.confirm_second_factor(page, '', state))
        page.get_by_role.return_value.first.click.assert_called_once()
        self.assertTrue(script.confirm_second_factor(self.page(), '', state))

    @patch('isolated_edge.time.time', return_value=60)
    def test_no_reuse_of_first_code(self, clock):
        page = self.page(field=True)
        state = {'confirmation_opened': True, 'first_totp_counter': 2}
        self.assertTrue(script.confirm_second_factor(page, '', state))
        page.evaluate.assert_not_called()

    @patch('isolated_edge.time.time', return_value=90)
    def test_submit_once_and_wait_for_field_to_disappear(self, clock):
        page = self.page(button=True, field=True)
        state = {'confirmation_opened': True, 'first_totp_counter': 2}
        secret = 'GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'
        self.assertTrue(script.confirm_second_factor(page, secret, state))
        self.assertTrue(script.confirm_second_factor(page, secret, state))
        page.evaluate.assert_called_once()
        self.assertFalse(script.confirm_second_factor(self.page(), secret, state))

    def test_totp_known_vector(self):
        self.assertEqual(script.totp_code('GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ', 59), '287082')

    def test_hoplite_waits(self):
        page = MagicMock()
        script.prepare_hoplite(page, {'confirmation_opened': True})
        page.goto.assert_not_called()


if __name__ == '__main__':
    unittest.main()
