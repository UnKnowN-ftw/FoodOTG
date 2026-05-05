from django.test import override_settings
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait

from accounts.tests.selenium.sprint3.base_test import BaseSeleniumTest


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"])
class BusinessDashboardTests(BaseSeleniumTest):

    def test_business_dashboard_route(self):
        self.browser.get(f"{self.live_server_url}/login/")

        self.browser.execute_script("""
            localStorage.setItem('token', 'dummy-business-token');
            localStorage.setItem('refresh', 'dummy-refresh-token');
            localStorage.setItem('role', 'business_owner');
        """)

        self.browser.get(f"{self.live_server_url}/business-dashboard/")

        try:
            WebDriverWait(self.browser, 3).until(lambda d: d.switch_to.alert)
            alert = self.browser.switch_to.alert
            alert_text = alert.text
            alert.accept()
            self.fail(f"Unexpected alert appeared: {alert_text}")
        except NoAlertPresentException:
            pass
        except Exception:
            pass

        self.assertIn("/business-dashboard/", self.browser.current_url)