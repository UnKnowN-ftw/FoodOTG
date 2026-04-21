from django.contrib.auth.models import User
from django.test import override_settings
from selenium.webdriver.support.ui import WebDriverWait

from accounts.models import UserProfile
from accounts.tests.selenium.sprint2.base_test import BaseSeleniumTest


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"])
class CustomerDashboardPageTests(BaseSeleniumTest):

    def test_customer_dashboard_page_loads(self):
        user = User.objects.create_user(
            username="customerdash@example.com",
            email="customerdash@example.com",
            password="testpass123"
        )
        UserProfile.objects.create(user=user, role="customer")

        # First open a same-origin page so localStorage can be set safely
        self.browser.get(f"{self.live_server_url}/login/")

        # Put values often required by dashboard scripts
        self.browser.execute_script("""
            localStorage.setItem('token', 'dummy-test-token');
            localStorage.setItem('refresh', 'dummy-refresh-token');
            localStorage.setItem('role', 'customer');
        """)

        # Now open dashboard
        self.browser.get(f"{self.live_server_url}/customer-dashboard/")

        WebDriverWait(self.browser, 10).until(
            lambda d: "/customer-dashboard/" in d.current_url
            or "/customer-login/" in d.current_url
            or "/login/" in d.current_url
        )

        current_url = self.browser.current_url

        # Main expectation: dashboard should open.
        # If it redirects, the page likely has JS auth protection.
        self.assertIn("/customer-dashboard/", current_url)