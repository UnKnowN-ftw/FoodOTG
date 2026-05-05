from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
import time


class BaseSeleniumTest(StaticLiveServerTestCase):
    def setUp(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        self.browser = webdriver.Chrome(options=options)

    def tearDown(self):
        self.browser.quit()

    def open_page(self, url):
        self.browser.get(f"{self.live_server_url}{url}")
        time.sleep(2)