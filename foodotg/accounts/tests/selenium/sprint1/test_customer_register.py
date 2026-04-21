from django.test import override_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from accounts.tests.selenium.sprint1.base_test import BaseSeleniumTest


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"])
class CustomerRegisterTests(BaseSeleniumTest):

    def wait_for_text(self, locator_type, locator, expected_text, timeout=10):
        WebDriverWait(self.browser, timeout).until(
            lambda d: expected_text in d.find_element(locator_type, locator).text
        )

    def test_customer_register_empty_fields_validation(self):
        self.browser.get(f"{self.live_server_url}/customer-register/")
        self.browser.find_element(By.TAG_NAME, "button").click()

        self.wait_for_text(By.ID, "msg", "All fields must be filled.")
        self.assertEqual(
            self.browser.find_element(By.ID, "msg").text,
            "All fields must be filled."
        )

    def test_customer_register_password_mismatch_validation(self):
        self.browser.get(f"{self.live_server_url}/customer-register/")

        self.browser.find_element(By.ID, "name").send_keys("Test Customer")
        self.browser.find_element(By.ID, "email").send_keys("customer1@example.com")
        self.browser.find_element(By.ID, "pass").send_keys("password123")
        self.browser.find_element(By.ID, "confirm_pass").send_keys("password999")
        self.browser.find_element(By.TAG_NAME, "button").click()

        self.wait_for_text(By.ID, "msg", "Passwords do not match.")
        self.assertEqual(
            self.browser.find_element(By.ID, "msg").text,
            "Passwords do not match."
        )

    def test_customer_register_short_password_validation(self):
        self.browser.get(f"{self.live_server_url}/customer-register/")

        self.browser.find_element(By.ID, "name").send_keys("Test Customer")
        self.browser.find_element(By.ID, "email").send_keys("customer2@example.com")
        self.browser.find_element(By.ID, "pass").send_keys("123")
        self.browser.find_element(By.ID, "confirm_pass").send_keys("123")
        self.browser.find_element(By.TAG_NAME, "button").click()

        self.wait_for_text(By.ID, "msg", "Security requires 6+ characters.")
        self.assertEqual(
            self.browser.find_element(By.ID, "msg").text,
            "Security requires 6+ characters."
        )