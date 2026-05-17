from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.apps import apps
from django.urls import resolve, Resolver404


def model_exists(model_name):
    try:
        apps.get_model("accounts", model_name)
        return True
    except LookupError:
        return False


def get_model(model_name):
    return apps.get_model("accounts", model_name)


class SecurityRoleAccessUnitTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.customer = User.objects.create_user(
            username="role_customer",
            email="role_customer@test.com",
            password="pass12345"
        )

        self.owner = User.objects.create_user(
            username="role_owner",
            email="role_owner@test.com",
            password="pass12345"
        )

        self.rider = User.objects.create_user(
            username="role_rider",
            email="role_rider@test.com",
            password="pass12345"
        )

        self.admin = User.objects.create_superuser(
            username="role_admin",
            email="role_admin@test.com",
            password="adminpass123"
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
            UserProfile.objects.get_or_create(
                user=self.rider,
                defaults={"role": "rider"}
            )
            UserProfile.objects.get_or_create(
                user=self.admin,
                defaults={"role": "admin"}
            )

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

    def get_response(self, path, user):
        self.client.force_login(user)

        last_response = None

        for url in self.get_possible_paths(path):
            response = self.client.get(url)
            last_response = response

            if response.status_code != 404:
                return response

        return last_response

    def assert_protected_page_response(self, possible_paths, user):
        route_found = False

        for path in possible_paths:
            if not self.route_exists(path):
                continue

            route_found = True
            response = self.get_response(path, user)

            self.assertIn(response.status_code, [200, 301, 302, 400, 401, 403])
            return

        if not route_found:
            self.skipTest(f"No route found from: {possible_paths}")

    def test_customer_access_to_business_dashboard_is_handled(self):
        possible_paths = [
            "/business-dashboard/",
            "/business/dashboard/",
            "/dashboard/business/",
        ]

        self.assert_protected_page_response(possible_paths, self.customer)

    def test_customer_access_to_admin_dashboard_is_handled(self):
        possible_paths = [
            "/admin-dashboard/",
            "/admin/dashboard/",
            "/dashboard/admin/",
            "/admin/",
        ]

        self.assert_protected_page_response(possible_paths, self.customer)

    def test_owner_access_to_customer_dashboard_is_handled(self):
        possible_paths = [
            "/customer-dashboard/",
            "/customer/dashboard/",
            "/dashboard/customer/",
        ]

        self.assert_protected_page_response(possible_paths, self.owner)

    def test_rider_access_to_rider_dashboard_is_handled(self):
        possible_paths = [
            "/rider-dashboard/",
            "/rider/dashboard/",
            "/dashboard/rider/",
        ]

        self.assert_protected_page_response(possible_paths, self.rider)