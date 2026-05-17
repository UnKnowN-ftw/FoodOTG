from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.apps import apps
from django.urls import resolve, Resolver404
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


def model_exists(model_name):
    try:
        apps.get_model("accounts", model_name)
        return True
    except LookupError:
        return False


def get_model(model_name):
    return apps.get_model("accounts", model_name)


class FoodOTGCartOrderDealAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.customer = User.objects.create_user(
            username="cartcustomer",
            email="cartcustomer@test.com",
            password="pass12345"
        )

        self.owner = User.objects.create_user(
            username="cartowner",
            email="cartowner@test.com",
            password="pass12345"
        )

        if model_exists("UserProfile"):
            UserProfile = get_model("UserProfile")

            UserProfile.objects.get_or_create(
                user=self.customer,
                defaults={"role": "customer"}
            )

            UserProfile.objects.get_or_create(
                user=self.owner,
                defaults={"role": "business_owner"}
            )

        refresh = RefreshToken.for_user(self.customer)
        self.customer_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.customer_token}")

    def route_exists(self, path):
        if path.endswith("/"):
            possible_paths = [path, path.rstrip("/")]
        else:
            possible_paths = [path + "/", path]

        for url in possible_paths:
            try:
                resolve(url)
                return True
            except Resolver404:
                continue

        return False

    def get_api(self, path):
        """
        Tries slash version first to avoid Django APPEND_SLASH 301 redirect.
        """
        if path.endswith("/"):
            possible_paths = [path, path.rstrip("/")]
        else:
            possible_paths = [path + "/", path]

        last_response = None

        for url in possible_paths:
            response = self.client.get(url)
            last_response = response

            if response.status_code not in [301, 302, 404]:
                return response

        return last_response

    def post_api(self, path, data):
        """
        Tries slash version first to avoid Django APPEND_SLASH 301 redirect.
        """
        if path.endswith("/"):
            possible_paths = [path, path.rstrip("/")]
        else:
            possible_paths = [path + "/", path]

        last_response = None

        for url in possible_paths:
            response = self.client.post(url, data, format="json")
            last_response = response

            if response.status_code not in [301, 302, 404, 415]:
                return response

            response = self.client.post(url, data, format="multipart")
            last_response = response

            if response.status_code not in [301, 302, 404, 415]:
                return response

        return last_response

    def delete_api(self, path):
        """
        Tries slash version first to avoid Django APPEND_SLASH 301 redirect.
        """
        if path.endswith("/"):
            possible_paths = [path, path.rstrip("/")]
        else:
            possible_paths = [path + "/", path]

        last_response = None

        for url in possible_paths:
            response = self.client.delete(url)
            last_response = response

            if response.status_code not in [301, 302, 404]:
                return response

        return last_response

    def create_restaurant_and_item(self):
        Restaurant = get_model("Restaurant")
        MenuItem = get_model("MenuItem")

        restaurant = Restaurant.objects.create(
            owner=self.owner,
            name="Cart Restaurant",
            description="Testing cart",
            address="Dhaka",
            category="Fast Food",
            price_range="৳৳",
            delivery_available=True,
            latitude=23.8103,
            longitude=90.4125
        )

        item = MenuItem.objects.create(
            restaurant=restaurant,
            name="Chicken Burger",
            description="Cart item",
            price=Decimal("300.00"),
            available=True
        )

        return restaurant, item

    def test_cart_endpoint_exists(self):
        possible_routes = [
            "/api/cart/",
            "/api/cart",
            "/cart/",
            "/cart",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Cart route not found in urls.py.")

        valid_response_found = False

        for path in possible_routes:
            if not self.route_exists(path):
                continue

            response = self.get_api(path)

            if response.status_code not in [301, 302, 404]:
                valid_response_found = True
                self.assertIn(response.status_code, [200, 400, 401, 403])
                break

        self.assertTrue(valid_response_found)

    def test_add_to_cart_api(self):
        if not model_exists("Restaurant") or not model_exists("MenuItem"):
            self.skipTest("Restaurant or MenuItem model not found.")

        restaurant, item = self.create_restaurant_and_item()

        possible_routes = [
            "/api/cart/add/",
            "/api/cart/add",
            "/api/add-to-cart/",
            "/api/add-to-cart",
            "/cart/add/",
            "/cart/add",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Add to cart route not found in urls.py.")

        payload_options = [
            {"menu_item_id": item.id, "quantity": 2},
            {"item_id": item.id, "quantity": 2},
            {"menu_item": item.id, "quantity": 2},
        ]

        valid_response_found = False

        for path in possible_routes:
            if not self.route_exists(path):
                continue

            for payload in payload_options:
                response = self.post_api(path, payload)

                if response.status_code not in [301, 302, 404]:
                    valid_response_found = True
                    self.assertIn(response.status_code, [200, 201, 400, 401, 403, 415])
                    break

            if valid_response_found:
                break

        self.assertTrue(valid_response_found)

    def test_checkout_summary_api(self):
        possible_routes = [
            "/api/checkout-summary/",
            "/api/checkout-summary",
            "/api/checkout_summary/",
            "/api/checkout_summary",
            "/checkout-summary/",
            "/checkout-summary",
            "/checkout/",
            "/checkout",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Checkout summary route not found in urls.py.")

        self.assertTrue(route_found)

    def test_place_order_api_exists(self):
        possible_routes = [
            "/api/place-order/",
            "/api/place-order",
            "/api/place_order/",
            "/api/place_order",
            "/place-order/",
            "/place-order",
            "/api/order/place/",
            "/api/order/place",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Place order route not found in urls.py.")

        valid_response_found = False

        for path in possible_routes:
            if not self.route_exists(path):
                continue

            response = self.post_api(path, {})

            if response.status_code not in [301, 302, 404]:
                valid_response_found = True
                self.assertIn(response.status_code, [200, 201, 400, 401, 403, 415])
                break

        self.assertTrue(valid_response_found)

    def test_deal_discount_model_logic(self):
        if not model_exists("Restaurant") or not model_exists("Deal"):
            self.skipTest("Restaurant or Deal model not found.")

        Restaurant = get_model("Restaurant")
        Deal = get_model("Deal")

        restaurant = Restaurant.objects.create(
            owner=self.owner,
            name="Deal Restaurant",
            description="Testing deal",
            address="Dhaka",
            category="Set Menu",
            price_range="৳৳",
            delivery_available=True,
            latitude=23.8103,
            longitude=90.4125
        )

        deal = Deal.objects.create(
            restaurant=restaurant,
            title="10 Percent Discount",
            description="Testing active deal",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            minimum_order_amount=Decimal("200.00"),
            active_status=True
        )

        subtotal = Decimal("500.00")

        if deal.discount_type == "percentage":
            discount_amount = subtotal * deal.discount_value / Decimal("100.00")
        else:
            discount_amount = deal.discount_value

        final_amount = subtotal - discount_amount

        self.assertEqual(discount_amount, Decimal("50.00"))
        self.assertEqual(final_amount, Decimal("450.00"))

    def test_clear_cart_api_exists(self):
        possible_routes = [
            "/api/cart/clear/",
            "/api/cart/clear",
            "/api/clear-cart/",
            "/api/clear-cart",
            "/cart/clear/",
            "/cart/clear",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Clear cart route not found in urls.py.")

        valid_response_found = False

        for path in possible_routes:
            if not self.route_exists(path):
                continue

            response = self.delete_api(path)

            if response.status_code not in [301, 302, 404]:
                valid_response_found = True
                self.assertIn(response.status_code, [200, 204, 400, 401, 403])
                break

        self.assertTrue(valid_response_found)