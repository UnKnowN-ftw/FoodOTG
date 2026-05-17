from django.test import TestCase, Client
from django.urls import resolve, Resolver404


class PageRouteUnitTests(TestCase):
    def setUp(self):
        self.client = Client()

    def route_exists(self, path):
        possible_paths = []

        if path.endswith("/"):
            possible_paths.append(path)
            possible_paths.append(path.rstrip("/"))
        else:
            possible_paths.append(path + "/")
            possible_paths.append(path)

        for url in possible_paths:
            try:
                resolve(url)
                return True
            except Resolver404:
                continue

        return False

    def assert_route_exists_from_list(self, paths, required=True):
        found = False
        checked_results = {}

        for path in paths:
            if not self.route_exists(path):
                checked_results[path] = "not registered"
                continue

            response = self.client.get(path)
            checked_results[path] = response.status_code

            if response.status_code == 404 and not path.endswith("/"):
                response = self.client.get(path + "/")
                checked_results[path + "/"] = response.status_code

            if response.status_code != 404:
                found = True
                self.assertIn(response.status_code, [200, 301, 302, 400, 401, 403])
                break

        if required:
            self.assertTrue(found, f"No valid route found from: {checked_results}")
        else:
            if not found:
                self.skipTest(f"Optional route not found. Checked: {checked_results}")

    def test_landing_page_route_if_available(self):
        possible_paths = [
            "/",
            "/home/",
            "/landing/",
            "/index/",
        ]

        self.assert_route_exists_from_list(possible_paths, required=False)

    def test_customer_login_page_route_exists(self):
        possible_paths = [
            "/customer-login/",
            "/customer/login/",
            "/login/customer/",
            "/login/",
        ]

        self.assert_route_exists_from_list(possible_paths)

    def test_business_login_page_route_exists(self):
        possible_paths = [
            "/business-login/",
            "/business/login/",
            "/login/business/",
            "/login/",
        ]

        self.assert_route_exists_from_list(possible_paths)

    def test_register_page_route_exists(self):
        possible_paths = [
            "/register/",
            "/customer-register/",
            "/signup/",
            "/customer/register/",
            "/business-register/",
            "/business/register/",
        ]

        self.assert_route_exists_from_list(possible_paths)

    def test_customer_dashboard_route_exists(self):
        possible_paths = [
            "/customer-dashboard/",
            "/customer/dashboard/",
            "/dashboard/customer/",
        ]

        self.assert_route_exists_from_list(possible_paths)

    def test_business_dashboard_route_exists(self):
        possible_paths = [
            "/business-dashboard/",
            "/business/dashboard/",
            "/dashboard/business/",
        ]

        self.assert_route_exists_from_list(possible_paths)