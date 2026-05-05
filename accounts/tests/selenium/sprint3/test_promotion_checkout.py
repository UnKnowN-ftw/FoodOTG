from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from accounts.models import UserProfile, Restaurant, MenuItem, Deal, Cart, CartItem


class PromotionCheckoutSeleniumTest(StaticLiveServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.driver = webdriver.Chrome()
        cls.wait = WebDriverWait(cls.driver, 10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer@test.com",
            email="customer@test.com",
            password="testpass123",
            first_name="Customer"
        )
        UserProfile.objects.create(user=self.customer, role="customer")

        self.owner = User.objects.create_user(
            username="owner@test.com",
            email="owner@test.com",
            password="testpass123"
        )
        UserProfile.objects.create(user=self.owner, role="business_owner")

        self.restaurant = Restaurant.objects.create(
            owner=self.owner,
            name="Test Restaurant",
            description="Food",
            address="Dhaka",
            category="Fast Food",
            price_range="৳৳"
        )

        self.item = MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Burger",
            price=Decimal("100.00"),
            available=True
        )

        Deal.objects.create(
            restaurant=self.restaurant,
            title="10% off!",
            description="Get 10% off for minimum 500tk spent.",
            active_status=True,
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            minimum_order_amount=Decimal("500.00")
        )

        self.cart = Cart.objects.create(user=self.customer)
        CartItem.objects.create(
            cart=self.cart,
            menu_item=self.item,
            quantity=5
        )

    def test_checkout_shows_discount(self):
        driver = self.driver

        driver.get(f"{self.live_server_url}/customer-login/")

        driver.execute_async_script(
            """
            const done = arguments[0];

            fetch('/api/login/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: 'customer@test.com',
                    password: 'testpass123'
                })
            })
            .then(response => response.json())
            .then(data => {
                localStorage.setItem('access', data.access);
                localStorage.setItem('token', data.access);
                localStorage.setItem('refresh', data.refresh);
                localStorage.setItem('role', data.role);
                done(data);
            })
            .catch(error => done({error: String(error)}));
            """
        )

        driver.get(f"{self.live_server_url}/checkout/")

        self.wait.until(
            EC.text_to_be_present_in_element(
                (By.ID, "checkoutContent"),
                "10% off!"
            )
        )

        content = driver.find_element(By.ID, "checkoutContent").text

        self.assertIn("10% off!", content)
        self.assertIn("Subtotal: ৳500", content)
        self.assertIn("Discount", content)
        self.assertIn("-৳50", content)
        self.assertIn("Grand Total", content)
        self.assertIn("৳450", content)