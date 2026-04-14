from django.test import override_settings
from selenium.webdriver.common.by import By

from accounts.tests.selenium.sprint1.base_test import BaseSeleniumTest


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"])
class LoginPageTests(BaseSeleniumTest):

    def test_login_selection_page_loads(self):
        self.browser.get(f"{self.live_server_url}/login/")
        heading = self.browser.find_element(By.TAG_NAME, "h2")
        self.assertIn("Welcome to FoodOTG", heading.text)

    def test_register_page_loads(self):
        self.browser.get(f"{self.live_server_url}/register/")
        heading = self.browser.find_element(By.TAG_NAME, "h2")
        self.assertIn("Create Customer Account", heading.text)

    def test_customer_login_page_loads(self):
        self.browser.get(f"{self.live_server_url}/customer-login/")
        heading = self.browser.find_element(By.TAG_NAME, "h2")
        self.assertIn("Customer Login", heading.text)

    def test_business_login_page_loads(self):
        self.browser.get(f"{self.live_server_url}/business-login/")
        heading = self.browser.find_element(By.TAG_NAME, "h2")
        self.assertIn("Business Owner Login", heading.text)

    def test_business_register_page_loads(self):
        self.browser.get(f"{self.live_server_url}/business-register/")
        heading = self.browser.find_element(By.TAG_NAME, "h2")
        self.assertIn("Register as Business Owner", heading.text)