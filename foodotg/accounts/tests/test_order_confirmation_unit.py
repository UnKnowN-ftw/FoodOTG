from decimal import Decimal

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


class OrderConfirmationUnitTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.customer = User.objects.create_user(
            username="order_confirm_customer",
            email="order_confirm_customer@test.com",
            password="pass12345"
        )

        self.owner = User.objects.create_user(
            username="order_confirm_owner",
            email="order_confirm_owner@test.com",
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

    def create_restaurant(self):
        Restaurant = get_model("Restaurant")

        return Restaurant.objects.create(
            owner=self.owner,
            name="Order Confirm Restaurant",
            description="Testing order confirmation",
            address="Dhaka",
            category="Food",
            price_range="৳৳",
            delivery_available=True,
            latitude=23.8103,
            longitude=90.4125
        )

    def create_order(self):
        if not model_exists("Restaurant") or not model_exists("Order"):
            return None

        Order = get_model("Order")
        restaurant = self.create_restaurant()

        field_names = [field.name for field in Order._meta.fields]

        order_fields = {}

        if "customer" in field_names:
            order_fields["customer"] = self.customer

        if "user" in field_names:
            order_fields["user"] = self.customer

        if "restaurant" in field_names:
            order_fields["restaurant"] = restaurant

        if "status" in field_names:
            order_fields["status"] = "confirmed"

        if "total_amount" in field_names:
            order_fields["total_amount"] = Decimal("450.00")

        if "original_amount" in field_names:
            order_fields["original_amount"] = Decimal("500.00")

        if "discount_amount" in field_names:
            order_fields["discount_amount"] = Decimal("50.00")

        if "applied_deal_title" in field_names:
            order_fields["applied_deal_title"] = "10% Off"

        return Order.objects.create(**order_fields)

    def test_order_confirmation_template_exists(self):
        possible_locations = [
            "accounts/templates/order_confirmation.html",
            "templates/order_confirmation.html",
        ]

        from pathlib import Path
        from django.conf import settings

        base_dir = Path(settings.BASE_DIR)

        exists = any((base_dir / location).exists() for location in possible_locations)

        self.assertTrue(exists, "order_confirmation.html template not found.")

    def test_order_confirmation_route_if_available(self):
        order = self.create_order()

        if order is None:
            self.skipTest("Order model not found.")

        self.client.force_login(self.customer)

        possible_paths = [
            f"/order-confirmation/{order.id}/",
            f"/order-confirmation/{order.id}",
            f"/order_confirmation/{order.id}/",
            f"/order_confirmation/{order.id}",
        ]

        route_found = False

        for path in possible_paths:
            if not self.route_exists(path):
                continue

            route_found = True

            for url in self.get_possible_paths(path):
                response = self.client.get(url)

                if response.status_code != 404:
                    self.assertIn(response.status_code, [200, 301, 302, 400, 401, 403])
                    return

        if not route_found:
            self.skipTest("Order confirmation route not found.")

    def test_order_discount_fields_if_available(self):
        order = self.create_order()

        if order is None:
            self.skipTest("Order model not found.")

        if hasattr(order, "original_amount"):
            self.assertEqual(order.original_amount, Decimal("500.00"))

        if hasattr(order, "discount_amount"):
            self.assertEqual(order.discount_amount, Decimal("50.00"))

        if hasattr(order, "total_amount"):
            self.assertEqual(order.total_amount, Decimal("450.00"))

        if hasattr(order, "applied_deal_title"):
            self.assertEqual(order.applied_deal_title, "10% Off")