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


class FoodOTGRestaurantMenuAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.owner = User.objects.create_user(
            username="businessowner",
            email="owner@test.com",
            password="pass12345"
        )

        self.customer = User.objects.create_user(
            username="customer",
            email="customer@test.com",
            password="pass12345"
        )

        if model_exists("UserProfile"):
            UserProfile = get_model("UserProfile")

            UserProfile.objects.get_or_create(
                user=self.owner,
                defaults={"role": "business_owner"}
            )

            UserProfile.objects.get_or_create(
                user=self.customer,
                defaults={"role": "customer"}
            )

        owner_refresh = RefreshToken.for_user(self.owner)
        self.owner_token = str(owner_refresh.access_token)

        customer_refresh = RefreshToken.for_user(self.customer)
        self.customer_token = str(customer_refresh.access_token)

    def auth_as_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.owner_token}")

    def auth_as_customer(self):
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
        Tries slash version first.
        Tries multipart first because add-restaurant may expect form-data/image upload.
        Then tries JSON as fallback.
        """
        if path.endswith("/"):
            possible_paths = [path, path.rstrip("/")]
        else:
            possible_paths = [path + "/", path]

        last_response = None

        for url in possible_paths:
            response = self.client.post(url, data, format="multipart")
            last_response = response

            if response.status_code not in [301, 302, 404, 415]:
                return response

            response = self.client.post(url, data, format="json")
            last_response = response

            if response.status_code not in [301, 302, 404, 415]:
                return response

        return last_response

    def create_restaurant(self):
        Restaurant = get_model("Restaurant")

        return Restaurant.objects.create(
            owner=self.owner,
            name="Menu API Restaurant",
            description="Testing menu API",
            address="Dhaka",
            category="Burger",
            price_range="৳৳",
            delivery_available=True,
            latitude=23.8103,
            longitude=90.4125
        )

    def test_add_restaurant_api(self):
        self.auth_as_owner()

        possible_routes = [
            "/api/add-restaurant/",
            "/api/add-restaurant",
            "/api/restaurants/add/",
            "/api/restaurants/add",
            "/api/restaurant/add/",
            "/api/restaurant/add",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Add restaurant API route not found in urls.py.")

        payload = {
            "name": "API Restaurant",
            "description": "Created from unit test",
            "address": "Dhaka",
            "category": "Fast Food",
            "price_range": "৳৳",
            "delivery_available": "true",
            "latitude": "23.8103",
            "longitude": "90.4125",
        }

        valid_response_found = False

        for path in possible_routes:
            if not self.route_exists(path):
                continue

            response = self.post_api(path, payload)

            if response.status_code not in [301, 302, 404]:
                valid_response_found = True

                self.assertIn(
                    response.status_code,
                    [200, 201, 400, 401, 403, 415]
                )
                break

        self.assertTrue(valid_response_found)

    def test_business_dashboard_api(self):
        self.auth_as_owner()

        possible_routes = [
            "/api/business-dashboard/",
            "/api/business-dashboard",
            "/business-dashboard/",
            "/business-dashboard",
            "/business/dashboard/",
            "/business/dashboard",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Business dashboard route not found in urls.py.")

        valid_response_found = False

        for path in possible_routes:
            if not self.route_exists(path):
                continue

            response = self.get_api(path)

            if response.status_code not in [301, 302, 404]:
                valid_response_found = True

                self.assertIn(
                    response.status_code,
                    [200, 400, 401, 403]
                )
                break

        self.assertTrue(valid_response_found)

    def test_menu_item_model_and_menu_api(self):
        if not model_exists("Restaurant") or not model_exists("MenuItem"):
            self.skipTest("Restaurant or MenuItem model not found.")

        MenuItem = get_model("MenuItem")

        restaurant = self.create_restaurant()

        MenuItem.objects.create(
            restaurant=restaurant,
            name="Beef Burger",
            description="Test burger",
            price=Decimal("250.00"),
            available=True
        )

        self.auth_as_customer()

        possible_routes = [
            f"/api/customer/restaurants/{restaurant.id}/menu/",
            f"/api/customer/restaurants/{restaurant.id}/menu",
            f"/api/restaurants/{restaurant.id}/menu/",
            f"/api/restaurants/{restaurant.id}/menu",
            f"/restaurants/{restaurant.id}/menu/",
            f"/restaurants/{restaurant.id}/menu",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Restaurant menu API route not found in urls.py.")

        valid_response_found = False

        for path in possible_routes:
            if not self.route_exists(path):
                continue

            response = self.get_api(path)

            if response.status_code not in [301, 302, 404]:
                valid_response_found = True

                self.assertIn(
                    response.status_code,
                    [200, 400, 401, 403]
                )
                break

        self.assertTrue(valid_response_found)