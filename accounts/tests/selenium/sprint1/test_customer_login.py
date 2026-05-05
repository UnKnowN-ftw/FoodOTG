from django.contrib.auth.models import User
from django.test import override_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from accounts.models import UserProfile
from accounts.tests.selenium.sprint1.base_test import BaseSeleniumTest


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"])
class CustomerLoginTests(BaseSeleniumTest):

    def wait_for_text(self, locator_type, locator, expected_text, timeout=10):
        WebDriverWait(self.browser, timeout).until(
            lambda d: expected_text in d.find_element(locator_type, locator).text
        )

    def test_customer_login_empty_fields_validation(self):
        self.browser.get(f"{self.live_server_url}/customer-login/")
        self.browser.find_element(By.TAG_NAME, "button").click()

        self.wait_for_text(By.ID, "msg", "All fields must be filled.")
        self.assertEqual(
            self.browser.find_element(By.ID, "msg").text,
            "All fields must be filled."
        )

    def test_customer_login_invalid_credentials(self):
        self.browser.get(f"{self.live_server_url}/customer-login/")

        self.browser.find_element(By.ID, "username").send_keys("wrong@example.com")
        self.browser.find_element(By.ID, "password").send_keys("wrongpass")
        self.browser.find_element(By.TAG_NAME, "button").click()

        self.wait_for_text(By.ID, "msg", "Invalid email or password")
        self.assertIn(
            "Invalid email or password",
            self.browser.find_element(By.ID, "msg").text
        )

    def test_customer_login_with_business_account_shows_role_error(self):
        user = User.objects.create_user(
            username="biz@example.com",
            email="biz@example.com",
            password="testpass123"
        )
        UserProfile.objects.create(user=user, role="business_owner")

        self.browser.get(f"{self.live_server_url}/customer-login/")
        self.browser.find_element(By.ID, "username").send_keys("biz@example.com")
        self.browser.find_element(By.ID, "password").send_keys("testpass123")
        self.browser.find_element(By.TAG_NAME, "button").click()

        self.wait_for_text(By.ID, "msg", "This account is not registered as a customer.")
        self.assertEqual(
            self.browser.find_element(By.ID, "msg").text,
            "This account is not registered as a customer."
        )

    def test_customer_login_success_redirects_to_dashboard(self):
        user = User.objects.create_user(
            username="customerok@example.com",
            email="customerok@example.com",
            password="testpass123"
        )
        UserProfile.objects.create(user=user, role="customer")

        self.browser.get(f"{self.live_server_url}/customer-login/")
        self.browser.find_element(By.ID, "username").send_keys("customerok@example.com")
        self.browser.find_element(By.ID, "password").send_keys("testpass123")
        self.browser.find_element(By.TAG_NAME, "button").click()

        WebDriverWait(self.browser, 10).until(
            EC.url_contains("/customer-dashboard/")
        )
        self.assertIn("/customer-dashboard/", self.browser.current_url)