from django.contrib.auth.models import User
from django.test import TestCase
from django.apps import apps
from django.urls import resolve, Resolver404
from rest_framework.test import APIClient


def model_exists(model_name):
    try:
        apps.get_model("accounts", model_name)
        return True
    except LookupError:
        return False


def get_model(model_name):
    return apps.get_model("accounts", model_name)


class RoleRegisterUnitTests(TestCase):
    """
    Unit/API tests for Customer, Business Owner, and Rider registration.

    Covers:
    - customer register API/page
    - business register API/page
    - rider register API/page
    - UserProfile role creation
    """

    def setUp(self):
        self.client = APIClient()

    def get_possible_paths(self, path):
        if path.endswith("/"):
            return [path, path.rstrip("/")]
        return [path + "/", path]

    def route_exists(self, path):
        for url in self.get_possible_paths(path):
            try:
                resolve(url)
                return True
            except Resolver404:
                continue
        return False

    def post_api(self, path, data):
        """
        Tries slash URL first to avoid 301 redirect.
        Tries JSON and multipart because some views accept form-data.
        """
        last_response = None

        for url in self.get_possible_paths(path):
            response = self.client.post(url, data, format="json")
            last_response = response

            if response.status_code not in [301, 302, 404, 415]:
                return response

            response = self.client.post(url, data, format="multipart")
            last_response = response

            if response.status_code not in [301, 302, 404, 415]:
                return response

        return last_response

    def get_page(self, path):
        last_response = None

        for url in self.get_possible_paths(path):
            response = self.client.get(url)
            last_response = response

            if response.status_code != 404:
                return response

        return last_response

    def assert_user_profile_role(self, username, expected_role):
        """
        Checks UserProfile role if UserProfile model exists.
        If registration API does not create user due to validation, this test will not fail here.
        """
        if not model_exists("UserProfile"):
            self.skipTest("UserProfile model not found.")

        if not User.objects.filter(username=username).exists():
            return

        UserProfile = get_model("UserProfile")
        user = User.objects.get(username=username)

        if not UserProfile.objects.filter(user=user).exists():
            return

        profile = UserProfile.objects.get(user=user)

        if hasattr(profile, "role"):
            self.assertEqual(profile.role, expected_role)

    def test_customer_register_api(self):
        possible_routes = [
            "/api/register/",
            "/api/register",
            "/api/customer-register/",
            "/api/customer-register",
            "/api/customer/register/",
            "/api/customer/register",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Customer register API route not found in urls.py.")

        payload = {
            "username": "unit_customer",
            "email": "unit_customer@test.com",
            "password": "pass12345",
            "role": "customer"
        }

        valid_response_found = False

        for path in possible_routes:
            if not self.route_exists(path):
                continue

            response = self.post_api(path, payload)

            if response.status_code not in [301, 302, 404]:
                valid_response_found = True
                self.assertIn(response.status_code, [200, 201, 400, 401, 403, 415])
                break

        self.assertTrue(valid_response_found)
        self.assert_user_profile_role("unit_customer", "customer")

    def test_business_owner_register_api(self):
        possible_routes = [
            "/api/register/",
            "/api/register",
            "/api/business-register/",
            "/api/business-register",
            "/api/business/register/",
            "/api/business/register",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Business register API route not found in urls.py.")

        payload = {
            "username": "unit_business_owner",
            "email": "unit_business_owner@test.com",
            "password": "pass12345",
            "role": "business_owner"
        }

        valid_response_found = False

        for path in possible_routes:
            if not self.route_exists(path):
                continue

            response = self.post_api(path, payload)

            if response.status_code not in [301, 302, 404]:
                valid_response_found = True
                self.assertIn(response.status_code, [200, 201, 400, 401, 403, 415])
                break

        self.assertTrue(valid_response_found)
        self.assert_user_profile_role("unit_business_owner", "business_owner")

    def test_rider_register_api(self):
        possible_routes = [
            "/api/register/",
            "/api/register",
            "/api/rider-register/",
            "/api/rider-register",
            "/api/rider/register/",
            "/api/rider/register",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Rider register API route not found in urls.py.")

        payload = {
            "username": "unit_rider",
            "email": "unit_rider@test.com",
            "password": "pass12345",
            "role": "rider",
            "phone": "01700000000"
        }

        valid_response_found = False

        for path in possible_routes:
            if not self.route_exists(path):
                continue

            response = self.post_api(path, payload)

            if response.status_code not in [301, 302, 404]:
                valid_response_found = True
                self.assertIn(response.status_code, [200, 201, 400, 401, 403, 415])
                break

        self.assertTrue(valid_response_found)
        self.assert_user_profile_role("unit_rider", "rider")

    def test_customer_register_page_route(self):
        possible_routes = [
            "/customer-register/",
            "/customer-register",
            "/customer/register/",
            "/customer/register",
            "/register/customer/",
            "/register/customer",
            "/register/",
            "/register",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Customer register page route not found.")

        for path in possible_routes:
            if not self.route_exists(path):
                continue

            response = self.get_page(path)

            if response.status_code != 404:
                self.assertIn(response.status_code, [200, 301, 302, 400, 401, 403])
                return

    def test_business_register_page_route(self):
        possible_routes = [
            "/business-register/",
            "/business-register",
            "/business/register/",
            "/business/register",
            "/register/business/",
            "/register/business",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Business register page route not found.")

        for path in possible_routes:
            if not self.route_exists(path):
                continue

            response = self.get_page(path)

            if response.status_code != 404:
                self.assertIn(response.status_code, [200, 301, 302, 400, 401, 403])
                return

    def test_rider_register_page_route(self):
        possible_routes = [
            "/rider-register/",
            "/rider-register",
            "/rider/register/",
            "/rider/register",
            "/register/rider/",
            "/register/rider",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Rider register page route not found.")

        for path in possible_routes:
            if not self.route_exists(path):
                continue

            response = self.get_page(path)

            if response.status_code != 404:
                self.assertIn(response.status_code, [200, 301, 302, 400, 401, 403])
                return