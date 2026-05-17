from pathlib import Path

from django.conf import settings
from django.test import TestCase


class StaticAssetReferenceUnitTests(TestCase):
    """
    Tests that important HTML templates reference their related CSS files.

    Some pages intentionally reuse shared CSS files or use inline CSS.
    Therefore, main pages are strict, but rider dashboard/order pages are soft checks.
    """

    def setUp(self):
        self.project_root = Path(settings.BASE_DIR)

        self.template_dirs = [
            self.project_root / "accounts" / "templates",
            self.project_root / "templates",
        ]

    def find_template(self, template_name):
        for template_dir in self.template_dirs:
            template_path = template_dir / template_name

            if template_path.exists():
                return template_path

        return None

    def get_template_content(self, template_name):
        template_path = self.find_template(template_name)

        if template_path is None:
            self.skipTest(f"{template_name} not found.")

        return template_path.read_text(encoding="utf-8", errors="ignore")

    def assert_template_references_any_css(self, template_name, css_names):
        content = self.get_template_content(template_name)

        found_css = False

        for css_name in css_names:
            if css_name in content:
                found_css = True
                break

        self.assertTrue(
            found_css,
            f"{template_name} does not reference any expected CSS file. "
            f"Expected one of: {css_names}"
        )

    def assert_template_has_css_or_inline_style(self, template_name, css_names):
        """
        Soft CSS check:
        Passes if the template references an expected CSS file
        OR contains inline/internal CSS.
        Useful for rider pages if they use <style> instead of separate CSS file.
        """
        content = self.get_template_content(template_name)

        has_expected_css = any(css_name in content for css_name in css_names)
        has_static_css_reference = ".css" in content
        has_inline_style_block = "<style" in content and "</style>" in content
        has_inline_style_attribute = "style=" in content

        self.assertTrue(
            has_expected_css
            or has_static_css_reference
            or has_inline_style_block
            or has_inline_style_attribute,
            f"{template_name} does not reference CSS and does not contain inline styles."
        )

    def test_login_template_references_css(self):
        self.assert_template_references_any_css(
            "login.html",
            ["login_styles.css"]
        )

    def test_register_template_references_css(self):
        self.assert_template_references_any_css(
            "register.html",
            [
                "register_styles.css",
                "login_styles.css",
            ]
        )

    def test_customer_login_template_references_css(self):
        self.assert_template_references_any_css(
            "customer_login.html",
            [
                "login_styles.css",
                "customer_login_styles.css",
            ]
        )

    def test_customer_register_template_references_css(self):
        self.assert_template_references_any_css(
            "customer_register.html",
            [
                "register_styles.css",
                "customer_register_styles.css",
                "login_styles.css",
            ]
        )

    def test_business_login_template_references_css(self):
        self.assert_template_references_any_css(
            "business_login.html",
            [
                "business_login_styles.css",
                "login_styles.css",
            ]
        )

    def test_business_register_template_references_css(self):
        self.assert_template_references_any_css(
            "business_register.html",
            [
                "business_register_styles.css",
                "register_styles.css",
                "login_styles.css",
            ]
        )

    def test_customer_dashboard_references_css(self):
        self.assert_template_references_any_css(
            "customer_dashboard.html",
            ["customer_dashboard_styles.css"]
        )

    def test_business_dashboard_references_css(self):
        self.assert_template_references_any_css(
            "business_dashboard.html",
            ["business_dashboard_styles.css"]
        )

    def test_admin_dashboard_references_css(self):
        self.assert_template_references_any_css(
            "admin_dashboard.html",
            ["admin_dashboard_styles.css"]
        )

    def test_admin_login_references_css(self):
        self.assert_template_references_any_css(
            "admin_login.html",
            [
                "admin_login_styles.css",
                "login_styles.css",
            ]
        )

    def test_checkout_references_css(self):
        self.assert_template_references_any_css(
            "checkout.html",
            ["checkout_styles.css"]
        )

    def test_order_confirmation_references_css(self):
        self.assert_template_references_any_css(
            "order_confirmation.html",
            ["order_confirmation_styles.css"]
        )

    def test_forgot_password_references_css(self):
        self.assert_template_references_any_css(
            "forgot_password.html",
            [
                "forgot_password_styles.css",
                "login_styles.css",
            ]
        )

    def test_reset_password_references_css(self):
        self.assert_template_references_any_css(
            "reset_password.html",
            [
                "reset_password_styles.css",
                "login_styles.css",
            ]
        )

    def test_rider_login_references_css(self):
        self.assert_template_references_any_css(
            "rider_login.html",
            [
                "rider_login_styles.css",
                "login_styles.css",
            ]
        )

    def test_rider_register_references_css(self):
        self.assert_template_references_any_css(
            "rider_register.html",
            [
                "rider_register_styles.css",
                "register_styles.css",
                "login_styles.css",
            ]
        )

    def test_rider_dashboard_has_css_or_inline_style_if_available(self):
        self.assert_template_has_css_or_inline_style(
            "rider_dashboard.html",
            [
                "rider_dashboard_styles.css",
                "rider_login_styles.css",
                "admin_dashboard_styles.css",
            ]
        )

    def test_rider_orders_has_css_or_inline_style_if_available(self):
        self.assert_template_has_css_or_inline_style(
            "rider_orders.html",
            [
                "rider_orders_styles.css",
                "rider_dashboard_styles.css",
                "admin_dashboard_styles.css",
            ]
        )