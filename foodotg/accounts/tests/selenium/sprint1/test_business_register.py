from django.test import override_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from accounts.tests.selenium.sprint1.base_test import BaseSeleniumTest


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"])
class BusinessRegisterTests(BaseSeleniumTest):

    def wait_for_text(self, locator_type, locator, expected_text, timeout=10):
        WebDriverWait(self.browser, timeout).until(
            lambda d: expected_text in d.find_element(locator_type, locator).text
        )

    def test_business_register_empty_fields_validation(self):
        self.browser.get(f"{self.live_server_url}/business-register/")
        self.browser.find_element(By.TAG_NAME, "button").click()

        self.wait_for_text(By.ID, "msg", "All fields must be filled.")
        self.assertEqual(
            self.browser.find_element(By.ID, "msg").text,
            "All fields must be filled."
        )

    def test_business_register_password_mismatch_validation(self):
        self.browser.get(f"{self.live_server_url}/business-register/")

        self.browser.find_element(By.ID, "name").send_keys("Owner One")
        self.browser.find_element(By.ID, "email").send_keys("owner1@example.com")
        self.browser.find_element(By.ID, "pass").send_keys("password123")
        self.browser.find_element(By.ID, "confirm_pass").send_keys("password456")
        self.browser.find_element(By.ID, "business_name").send_keys("Food Corner")
        self.browser.find_element(By.ID, "description").send_keys("Nice food")
        self.browser.find_element(By.ID, "address").send_keys("Dhaka")
        self.browser.find_element(By.TAG_NAME, "button").click()

        self.wait_for_text(By.ID, "msg", "Passwords do not match.")
        self.assertEqual(
            self.browser.find_element(By.ID, "msg").text,
            "Passwords do not match."
        )