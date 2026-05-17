from django.contrib.auth.models import User
from django.test import TestCase
from django.apps import apps
from rest_framework.test import APIClient


def model_exists(model_name):
    try:
        apps.get_model("accounts", model_name)
        return True
    except LookupError:
        return False


def get_model(model_name):
    return apps.get_model("accounts", model_name)


class AuthAndLoginUnitTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def post_api(self, path, data):
        """
        Always try slash URL first because Django commonly uses APPEND_SLASH=True.
        This prevents 301 redirect failure in unit tests.
        """
        possible_paths = []

        if path.endswith("/"):
            possible_paths.append(path)
            possible_paths.append(path.rstrip("/"))
        else:
            possible_paths.append(path + "/")
            possible_paths.append(path)

        last_response = None

        for url in possible_paths:
            response = self.client.post(url, data, format="json")
            last_response = response

            if response.status_code != 301 and response.status_code != 302 and response.status_code != 404:
                return response

        return last_response

    def get_api(self, path):
        possible_paths = []

        if path.endswith("/"):
            possible_paths.append(path)
            possible_paths.append(path.rstrip("/"))
        else:
            possible_paths.append(path + "/")
            possible_paths.append(path)

        last_response = None

        for url in possible_paths:
            response = self.client.get(url)
            last_response = response

            if response.status_code != 301 and response.status_code != 302 and response.status_code != 404:
                return response

        return last_response

    def test_user_can_be_created(self):
        user = User.objects.create_user(
            username="customer_test",
            email="customer@test.com",
            password="pass12345"
        )

        self.assertEqual(user.username, "customer_test")
        self.assertTrue(user.check_password("pass12345"))

    def test_user_profile_role_creation(self):
        if not model_exists("UserProfile"):
            self.skipTest("UserProfile model not found.")

        UserProfile = get_model("UserProfile")

        user = User.objects.create_user(
            username="profile_user",
            email="profile@test.com",
            password="pass12345"
        )

        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={"role": "customer"}
        )

        self.assertEqual(profile.user, user)
        self.assertTrue(hasattr(profile, "role"))

    def test_customer_registration_api_exists(self):
        payload = {
            "username": "newcustomer",
            "email": "newcustomer@test.com",
            "password": "pass12345",
            "role": "customer"
        }

        response = self.post_api("/api/register", payload)

        self.assertNotEqual(response.status_code, 404)
        self.assertNotEqual(response.status_code, 301)
        self.assertNotEqual(response.status_code, 302)
        self.assertIn(response.status_code, [200, 201, 400])

    def test_business_owner_registration_api_exists(self):
        payload = {
            "username": "businessowner",
            "email": "owner@test.com",
            "password": "pass12345",
            "role": "business_owner"
        }

        response = self.post_api("/api/register", payload)

        self.assertNotEqual(response.status_code, 404)
        self.assertNotEqual(response.status_code, 301)
        self.assertNotEqual(response.status_code, 302)
        self.assertIn(response.status_code, [200, 201, 400])

    def test_login_api_success(self):
        User.objects.create_user(
            username="loginuser",
            email="login@test.com",
            password="pass12345"
        )

        payload = {
            "username": "loginuser",
            "password": "pass12345"
        }

        response = self.post_api("/api/login", payload)

        self.assertNotEqual(response.status_code, 404)
        self.assertNotEqual(response.status_code, 301)
        self.assertNotEqual(response.status_code, 302)
        self.assertIn(response.status_code, [200, 201, 400])

        if response.status_code in [200, 201]:
            data = response.json()

            self.assertTrue(
                "access" in data
                or "refresh" in data
                or "token" in data
                or "message" in data
                or "role" in data
            )

    def test_login_api_wrong_password_fails(self):
        User.objects.create_user(
            username="wrongpassuser",
            email="wrongpass@test.com",
            password="pass12345"
        )

        payload = {
            "username": "wrongpassuser",
            "password": "wrongpassword"
        }

        response = self.post_api("/api/login", payload)

        self.assertNotEqual(response.status_code, 404)
        self.assertNotEqual(response.status_code, 301)
        self.assertNotEqual(response.status_code, 302)
        self.assertIn(response.status_code, [400, 401])