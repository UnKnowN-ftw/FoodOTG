from django.test import override_settings

from accounts.tests.selenium.sprint3.base_test import BaseSeleniumTest


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"])
class BusinessDashboardTests(BaseSeleniumTest):

    def test_business_dashboard_route(self):
        self.browser.get(f"{self.live_server_url}/business-dashboard/")

        self.assertTrue(
            "/business-dashboard/" in self.browser.current_url
            or "/business-login/" in self.browser.current_url
        )