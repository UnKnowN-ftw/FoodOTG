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


class RegistrationUnitTests(TestCase):

    def setUp(self):
        self.client = APIClient()

    # -------------------------------------------------
    # Helper Function
    # -------------------------------------------------

    def post_api(self, path, data):

        possible_paths = []

        if path.endswith("/"):
            possible_paths.append(path)
            possible_paths.append(path.rstrip("/"))
        else:
            possible_paths.append(path + "/")
            possible_paths.append(path)

        last_response = None

        for url in possible_paths:

            response = self.client.post(
                url,
                data,
                format="json"
            )

            last_response = response

            if response.status_code not in [301, 302, 404]:
                return response

        return last_response

    # -------------------------------------------------
    # CUSTOMER REGISTRATION TESTS
    # -------------------------------------------------

    def test_customer_registration_success(self):

        payload = {
            "name": "Customer User",
            "email": "customer@test.com",
            "password": "pass12345",
            "role": "customer"
        }

        response = self.post_api(
            "/api/register",
            payload
        )

        self.assertNotEqual(response.status_code, 404)

        self.assertIn(
            response.status_code,
            [200, 201]
        )

        user_exists = User.objects.filter(
            email="customer@test.com"
        ).exists()

        self.assertTrue(user_exists)

    def test_customer_registration_duplicate_email(self):

        User.objects.create_user(
            username="customer@test.com",
            email="customer@test.com",
            password="pass12345"
        )

        payload = {
            "name": "Another Customer",
            "email": "customer@test.com",
            "password": "pass12345",
            "role": "customer"
        }

        response = self.post_api(
            "/api/register",
            payload
        )

        self.assertIn(
            response.status_code,
            [400, 409]
        )

    def test_customer_registration_missing_fields(self):

        payload = {
            "name": "",
            "email": "",
            "password": "",
            "role": "customer"
        }

        response = self.post_api(
            "/api/register",
            payload
        )

        self.assertIn(
            response.status_code,
            [400]
        )

    def test_customer_registration_short_password(self):

        payload = {
            "name": "Short Pass",
            "email": "short@test.com",
            "password": "123",
            "role": "customer"
        }

        response = self.post_api(
            "/api/register",
            payload
        )

        self.assertIn(
            response.status_code,
            [400]
        )

    # -------------------------------------------------
    # BUSINESS OWNER REGISTRATION TESTS
    # -------------------------------------------------

    def test_business_owner_registration_success(self):

        payload = {
            "name": "Business Owner",
            "email": "owner@test.com",
            "password": "pass12345",
            "role": "business_owner",

            "business_name": "Food Palace",
            "description": "Best food",
            "address": "Dhaka",
            "category": "Fast Food",
            "price_range": "৳৳"
        }

        response = self.post_api(
            "/api/register",
            payload
        )

        self.assertNotEqual(response.status_code, 404)

        self.assertIn(
            response.status_code,
            [200, 201]
        )

        user_exists = User.objects.filter(
            email="owner@test.com"
        ).exists()

        self.assertTrue(user_exists)


    def test_business_registration_allows_empty_business_name(self):

        payload = {
            "name": "Business Owner",
            "email": "owner@test.com",
            "password": "pass12345",
            "role": "business_owner",

            "business_name": "",
            "description": "Best food",
            "address": "Dhaka",
            "category": "Fast Food",
            "price_range": "৳৳"
        }

        response = self.post_api(
            "/api/register",
            payload
        )

        self.assertNotEqual(response.status_code, 404)

        self.assertIn(
            response.status_code,
            [200, 201]
        )

        user_exists = User.objects.filter(
            email="owner@test.com"
        ).exists()

        self.assertTrue(user_exists)

    def test_business_registration_duplicate_email(self):

        User.objects.create_user(
            username="owner@test.com",
            email="owner@test.com",
            password="pass12345"
        )

        payload = {
            "name": "Business Owner",
            "email": "owner@test.com",
            "password": "pass12345",
            "role": "business_owner"
        }

        response = self.post_api(
            "/api/register",
            payload
        )

        self.assertIn(
            response.status_code,
            [400, 409]
        )

    # -------------------------------------------------
    # RIDER REGISTRATION TESTS
    # -------------------------------------------------

    def test_rider_registration_success(self):

        payload = {
            "name": "Rider One",
            "email": "rider@test.com",
            "password": "pass12345",
            "role": "rider"
        }

        response = self.post_api(
            "/api/register",
            payload
        )

        self.assertNotEqual(response.status_code, 404)

        self.assertIn(
            response.status_code,
            [200, 201]
        )

        user_exists = User.objects.filter(
            email="rider@test.com"
        ).exists()

        self.assertTrue(user_exists)

    def test_rider_registration_invalid_email(self):

        payload = {
            "name": "Rider One",
            "email": "invalid-email",
            "password": "pass12345",
            "role": "rider"
        }

        response = self.post_api(
            "/api/register",
            payload
        )

        self.assertIn(
            response.status_code,
            [400]
        )

    def test_rider_registration_short_password(self):

        payload = {
            "name": "Rider One",
            "email": "rider@test.com",
            "password": "123",
            "role": "rider"
        }

        response = self.post_api(
            "/api/register",
            payload
        )

        self.assertIn(
            response.status_code,
            [400]
        )

    # -------------------------------------------------
    # PASSWORD HASH TEST
    # -------------------------------------------------

    def test_password_is_hashed(self):

        user = User.objects.create_user(
            username="hashuser",
            email="hash@test.com",
            password="pass12345"
        )

        self.assertNotEqual(
            user.password,
            "pass12345"
        )

        self.assertTrue(
            user.check_password("pass12345")
        )

    # -------------------------------------------------
    # USER PROFILE ROLE TEST
    # -------------------------------------------------

    def test_user_profile_role_creation(self):

        if not model_exists("UserProfile"):
            self.skipTest(
                "UserProfile model not found."
            )

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

        self.assertEqual(
            profile.user,
            user
        )

        self.assertTrue(
            hasattr(profile, "role")
        )

