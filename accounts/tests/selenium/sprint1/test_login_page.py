from django.test import override_settings
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from accounts.tests.selenium.sprint1.base_test import BaseSeleniumTest


@override_settings(ALLOWED_HOSTS=["localhost", "127.0.0.1", "testserver"])
class LoginPageTests(BaseSeleniumTest):

    def open_page_and_wait(self, url, timeout=10):
        self.browser.get(f"{self.live_server_url}{url}")
        WebDriverWait(self.browser, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def test_login_selection_page_loads(self):
        self.open_page_and_wait("/login/")
        self.assertIn("Welcome to FoodOTG", self.browser.page_source)

    def test_register_page_loads(self):
        self.open_page_and_wait("/register/")
        self.assertIn("/register/", self.browser.current_url)
        self.assertIn("FoodOTG", self.browser.title)

    def test_customer_login_page_loads(self):
        self.open_page_and_wait("/customer-login/")
        self.assertIn("Customer Login", self.browser.page_source)

    def test_business_login_page_loads(self):
        self.open_page_and_wait("/business-login/")
        self.assertIn("Business Owner Login", self.browser.page_source)

    def test_business_register_page_loads(self):
        self.open_page_and_wait("/business-register/")
        self.assertIn("Register as Business Owner", self.browser.page_source)