from accounts.tests.selenium.sprint4.base_test import BaseSeleniumTest

class CheckoutPageTests(BaseSeleniumTest):

    def test_checkout_page_load(self):
        self.open_page("/checkout/")

        # inject fake login
        self.browser.execute_script("""
            localStorage.setItem("token", "dummy");
            localStorage.setItem("role", "customer");
        """)

        self.browser.get(self.live_server_url + "/checkout/")

        self.assertIn("Checkout", self.browser.page_source)