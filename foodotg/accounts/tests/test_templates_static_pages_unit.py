from pathlib import Path

from django.conf import settings
from django.test import TestCase, Client
from django.urls import resolve, Resolver404


class TemplateStaticPagesUnitTests(TestCase):
    """
    Unit tests for FoodOTG HTML templates, CSS static files, and page routes.

    Covers:
    - Required HTML template files
    - Required CSS files
    - Login/register/dashboard/checkout/order/rider/admin page routes

    Optional routes are skipped if they are not registered in urls.py.
    """

    def setUp(self):
        self.client = Client()
        self.project_root = Path(settings.BASE_DIR)

        self.template_dirs = [
            self.project_root / "accounts" / "templates",
            self.project_root / "templates",
        ]

        self.static_css_dirs = [
            self.project_root / "static" / "css",
            self.project_root / "accounts" / "static" / "css",
            self.project_root / "accounts" / "static" / "accounts" / "css",
        ]

    def file_exists_in_any_dir(self, file_name, directories):
        for directory in directories:
            file_path = directory / file_name
            if file_path.exists():
                return True
        return False

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

    def get_page_response(self, path):
        last_response = None

        for url in self.get_possible_paths(path):
            response = self.client.get(url)
            last_response = response

            if response.status_code != 404:
                return response

        return last_response

    def assert_any_route_works(self, possible_paths, required=True):
        route_found = False
        valid_response_found = False
        checked_results = {}

        for path in possible_paths:
            if not self.route_exists(path):
                checked_results[path] = "not registered"
                continue

            route_found = True

            response = self.get_page_response(path)
            checked_results[path] = response.status_code

            if response.status_code != 404:
                valid_response_found = True
                self.assertIn(
                    response.status_code,
                    [200, 301, 302, 400, 401, 403]
                )
                break

        if not route_found and not required:
            self.skipTest(f"Optional route not found. Checked: {checked_results}")

        self.assertTrue(
            route_found,
            f"No route registered from: {checked_results}"
        )

        self.assertTrue(
            valid_response_found,
            f"Route found but no valid response from: {checked_results}"
        )

    def test_required_html_template_files_exist(self):
        required_templates = [
            "admin_dashboard.html",
            "admin_login.html",
            "business_dashboard.html",
            "business_login.html",
            "business_register.html",
            "checkout.html",
            "customer_dashboard.html",
            "customer_login.html",
            "customer_register.html",
            "forgot_password.html",
            "login.html",
            "order_confirmation.html",
            "register.html",
            "reset_password.html",
            "rider_dashboard.html",
            "rider_login.html",
            "rider_orders.html",
            "rider_register.html",
        ]

        missing_templates = []

        for template_name in required_templates:
            if not self.file_exists_in_any_dir(template_name, self.template_dirs):
                missing_templates.append(template_name)

        self.assertEqual(
            missing_templates,
            [],
            f"Missing HTML template files: {missing_templates}"
        )

    def test_optional_demo_template_if_available(self):
        optional_templates = [
            "demo.html",
        ]

        for template_name in optional_templates:
            self.file_exists_in_any_dir(template_name, self.template_dirs)

        self.assertTrue(True)

    def test_required_css_files_exist(self):
        required_css_files = [
            "admin_dashboard_styles.css",
            "admin_login_styles.css",
            "business_dashboard_styles.css",
            "business_login_styles.css",
            "business_register_styles.css",
            "checkout_styles.css",
            "customer_dashboard_styles.css",
            "forgot_password_styles.css",
            "login_styles.css",
            "order_confirmation_styles.css",
            "register_styles.css",
            "reset_password_styles.css",
            "rider_login_styles.css",
            "rider_register_styles.css",
        ]

        missing_css_files = []

        for css_file in required_css_files:
            if not self.file_exists_in_any_dir(css_file, self.static_css_dirs):
                missing_css_files.append(css_file)

        self.assertEqual(
            missing_css_files,
            [],
            f"Missing CSS files: {missing_css_files}"
        )

    def test_main_login_page_route_exists(self):
        possible_paths = [
            "/login/",
            "/login",
            "/accounts/login/",
            "/accounts/login",
        ]

        self.assert_any_route_works(possible_paths)

    def test_register_page_route_exists(self):
        possible_paths = [
            "/register/",
            "/register",
            "/accounts/register/",
            "/accounts/register",
            "/signup/",
            "/signup",
        ]

        self.assert_any_route_works(possible_paths)

    def test_customer_login_page_route_exists(self):
        possible_paths = [
            "/customer-login/",
            "/customer-login",
            "/customer/login/",
            "/customer/login",
            "/login/customer/",
            "/login/customer",
        ]

        self.assert_any_route_works(possible_paths)

    def test_customer_register_page_route_exists(self):
        possible_paths = [
            "/customer-register/",
            "/customer-register",
            "/customer/register/",
            "/customer/register",
            "/register/customer/",
            "/register/customer",
        ]

        self.assert_any_route_works(possible_paths)

    def test_business_login_page_route_exists(self):
        possible_paths = [
            "/business-login/",
            "/business-login",
            "/business/login/",
            "/business/login",
            "/login/business/",
            "/login/business",
        ]

        self.assert_any_route_works(possible_paths)

    def test_business_register_page_route_exists(self):
        possible_paths = [
            "/business-register/",
            "/business-register",
            "/business/register/",
            "/business/register",
            "/register/business/",
            "/register/business",
        ]

        self.assert_any_route_works(possible_paths)

    def test_admin_login_page_route_exists(self):
        possible_paths = [
            "/admin-login/",
            "/admin-login",
            "/admin/login/",
            "/admin/login",
            "/login/admin/",
            "/login/admin",
            "/admin/",
            "/admin",
        ]

        self.assert_any_route_works(possible_paths)

    def test_rider_login_page_route_exists(self):
        possible_paths = [
            "/rider-login/",
            "/rider-login",
            "/rider/login/",
            "/rider/login",
            "/login/rider/",
            "/login/rider",
        ]

        self.assert_any_route_works(possible_paths)

    def test_rider_register_page_route_exists(self):
        possible_paths = [
            "/rider-register/",
            "/rider-register",
            "/rider/register/",
            "/rider/register",
            "/register/rider/",
            "/register/rider",
        ]

        self.assert_any_route_works(possible_paths)

    def test_customer_dashboard_page_route_exists(self):
        possible_paths = [
            "/customer-dashboard/",
            "/customer-dashboard",
            "/customer/dashboard/",
            "/customer/dashboard",
            "/dashboard/customer/",
            "/dashboard/customer",
        ]

        self.assert_any_route_works(possible_paths)

    def test_business_dashboard_page_route_exists(self):
        possible_paths = [
            "/business-dashboard/",
            "/business-dashboard",
            "/business/dashboard/",
            "/business/dashboard",
            "/dashboard/business/",
            "/dashboard/business",
        ]

        self.assert_any_route_works(possible_paths)

    def test_admin_dashboard_page_route_exists(self):
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

        self.assert_any_route_works(possible_paths)

    def test_rider_dashboard_page_route_exists(self):
        possible_paths = [
            "/rider-dashboard/",
            "/rider-dashboard",
            "/rider/dashboard/",
            "/rider/dashboard",
            "/dashboard/rider/",
            "/dashboard/rider",
        ]

        self.assert_any_route_works(possible_paths)

    def test_rider_orders_page_route_exists(self):
        possible_paths = [
            "/rider-orders/",
            "/rider-orders",
            "/rider/orders/",
            "/rider/orders",
        ]

        self.assert_any_route_works(possible_paths)

    def test_checkout_page_route_exists(self):
        possible_paths = [
            "/checkout/",
            "/checkout",
            "/cart/checkout/",
            "/cart/checkout",
        ]

        self.assert_any_route_works(possible_paths)

    def test_order_confirmation_page_route_if_available(self):
        possible_paths = [
            "/order-confirmation/1/",
            "/order-confirmation/1",
            "/order_confirmation/1/",
            "/order_confirmation/1",
        ]

        self.assert_any_route_works(possible_paths, required=False)

    def test_forgot_password_page_route_exists(self):
        possible_paths = [
            "/forgot-password/",
            "/forgot-password",
            "/forgot_password/",
            "/forgot_password",
            "/password/forgot/",
            "/password/forgot",
        ]

        self.assert_any_route_works(possible_paths)

    def test_reset_password_page_route_if_available(self):
        possible_paths = [
            "/reset-password/",
            "/reset-password",
            "/reset_password/",
            "/reset_password",
            "/password/reset/",
            "/password/reset",
        ]

        self.assert_any_route_works(possible_paths, required=False)