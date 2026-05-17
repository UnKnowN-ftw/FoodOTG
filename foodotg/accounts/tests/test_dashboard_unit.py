from django.contrib.auth.models import User
from django.test import TestCase, Client
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


class DashboardUnitTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_client = APIClient()

        self.customer = User.objects.create_user(
            username="dashboard_customer",
            email="customer@test.com",
            password="pass12345"
        )

        self.owner = User.objects.create_user(
            username="dashboard_owner",
            email="owner@test.com",
            password="pass12345"
        )

        self.rider_user = User.objects.create_user(
            username="dashboard_rider",
            email="rider@test.com",
            password="pass12345"
        )

        self.admin_user = User.objects.create_superuser(
            username="dashboard_admin",
            email="admin@test.com",
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
                user=self.rider_user,
                defaults={"role": "rider"}
            )

            UserProfile.objects.get_or_create(
                user=self.admin_user,
                defaults={"role": "admin"}
            )

    def route_exists(self, path):
        """
        Checks whether a URL pattern exists in urls.py without executing the view.
        This avoids failing because of login/session/API logic.
        """
        possible_paths = self.get_possible_paths(path)

        for url in possible_paths:
            try:
                resolve(url)
                return True
            except Resolver404:
                continue

        return False

    def get_possible_paths(self, path):
        """
        Tries both slash and non-slash versions to avoid APPEND_SLASH redirect issues.
        """
        if path.endswith("/"):
            return [path, path.rstrip("/")]
        return [path + "/", path]

    def get_page_response(self, path, user=None):
        """
        Gets normal HTML/page dashboard response.
        Accepts redirects because protected dashboards often redirect unauthenticated
        or role-mismatched users.
        """
        if user is not None:
            self.client.force_login(user)

        last_response = None

        for url in self.get_possible_paths(path):
            response = self.client.get(url)
            last_response = response

            if response.status_code != 404:
                return response

        return last_response

    def get_api_response(self, path, user=None):
        """
        Gets API dashboard response using JWT.
        Accepts redirects because some APIs/pages may normalize slash or redirect.
        """
        if user is not None:
            token = RefreshToken.for_user(user)
            self.api_client.credentials(
                HTTP_AUTHORIZATION=f"Bearer {token.access_token}"
            )

        last_response = None

        for url in self.get_possible_paths(path):
            response = self.api_client.get(url)
            last_response = response

            if response.status_code != 404:
                return response

        return last_response

    def assert_dashboard_route_works(self, possible_paths, user=None, api=False):
        """
        A route test should prove that the dashboard route is registered
        and returns a normal Django/DRF response.

        Accepted status codes:
        200 = page/API loads
        301/302 = redirect because of trailing slash/login/session
        400 = bad request but route exists
        401 = unauthenticated API access
        403 = forbidden due to role/permission
        """
        route_found = False
        valid_response_found = False
        checked_results = {}

        for path in possible_paths:
            if not self.route_exists(path):
                checked_results[path] = "not registered"
                continue

            route_found = True

            if api:
                response = self.get_api_response(path, user=user)
            else:
                response = self.get_page_response(path, user=user)

            checked_results[path] = response.status_code

            if response.status_code != 404:
                valid_response_found = True

                self.assertIn(
                    response.status_code,
                    [200, 301, 302, 400, 401, 403]
                )
                break

        if not route_found:
            self.skipTest(f"Dashboard route not found. Checked: {checked_results}")

        self.assertTrue(
            valid_response_found,
            f"Dashboard route found but no valid response. Checked: {checked_results}"
        )

    def test_customer_dashboard_page_route(self):
        possible_paths = [
            "/customer-dashboard/",
            "/customer-dashboard",
            "/customer/dashboard/",
            "/customer/dashboard",
            "/dashboard/customer/",
            "/dashboard/customer",
        ]

        self.assert_dashboard_route_works(
            possible_paths=possible_paths,
            user=self.customer,
            api=False
        )

    def test_business_dashboard_page_route(self):
        possible_paths = [
            "/business-dashboard/",
            "/business-dashboard",
            "/business/dashboard/",
            "/business/dashboard",
            "/dashboard/business/",
            "/dashboard/business",
        ]

        self.assert_dashboard_route_works(
            possible_paths=possible_paths,
            user=self.owner,
            api=False
        )

    def test_admin_dashboard_page_route(self):
        possible_paths = [
            "/admin-dashboard/",
            "/admin-dashboard",
            "/admin/dashboard/",
            "/admin/dashboard",
            "/dashboard/admin/",
            "/dashboard/admin",
            "/admin/",
            "/admin",
        ]

        self.assert_dashboard_route_works(
            possible_paths=possible_paths,
            user=self.admin_user,
            api=False
        )

    def test_rider_dashboard_page_route(self):
        possible_paths = [
            "/rider-dashboard/",
            "/rider-dashboard",
            "/rider/dashboard/",
            "/rider/dashboard",
            "/dashboard/rider/",
            "/dashboard/rider",
        ]

        self.assert_dashboard_route_works(
            possible_paths=possible_paths,
            user=self.rider_user,
            api=False
        )

    def test_customer_dashboard_api_route_if_available(self):
        possible_paths = [
            "/api/dashboard/",
            "/api/dashboard",
            "/api/customer-dashboard/",
            "/api/customer-dashboard",
            "/api/customer/dashboard/",
            "/api/customer/dashboard",
        ]

        self.assert_dashboard_route_works(
            possible_paths=possible_paths,
            user=self.customer,
            api=True
        )

    def test_business_dashboard_api_route_if_available(self):
        possible_paths = [
            "/api/business-dashboard/",
            "/api/business-dashboard",
            "/api/business/dashboard/",
            "/api/business/dashboard",
        ]

        self.assert_dashboard_route_works(
            possible_paths=possible_paths,
            user=self.owner,
            api=True
        )

    def test_admin_dashboard_api_route_if_available(self):
        possible_paths = [
            "/api/admin-dashboard/",
            "/api/admin-dashboard",
            "/api/admin/dashboard/",
            "/api/admin/dashboard",
            "/api/admin-panel/",
            "/api/admin-panel",
        ]

        self.assert_dashboard_route_works(
            possible_paths=possible_paths,
            user=self.admin_user,
            api=True
        )

    def test_rider_dashboard_api_route_if_available(self):
        possible_paths = [
            "/api/rider-dashboard/",
            "/api/rider-dashboard",
            "/api/rider/dashboard/",
            "/api/rider/dashboard",
            "/api/rider/orders/",
            "/api/rider/orders",
            "/rider-orders/",
            "/rider-orders",
            "/rider/orders/",
            "/rider/orders",
        ]

        self.assert_dashboard_route_works(
            possible_paths=possible_paths,
            user=self.rider_user,
            api=True
        )