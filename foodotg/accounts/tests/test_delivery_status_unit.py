from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.apps import apps
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


class DeliveryStatusUnitTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.customer = User.objects.create_user(
            username="delivery_customer",
            email="deliverycustomer@test.com",
            password="pass12345"
        )

        self.owner = User.objects.create_user(
            username="delivery_owner",
            email="deliveryowner@test.com",
            password="pass12345"
        )

        self.rider_user = User.objects.create_user(
            username="delivery_rider",
            email="deliveryrider@test.com",
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

            UserProfile.objects.get_or_create(
                user=self.rider_user,
                defaults={"role": "rider"}
            )

        token = RefreshToken.for_user(self.rider_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def create_restaurant(self):
        Restaurant = get_model("Restaurant")

        return Restaurant.objects.create(
            owner=self.owner,
            name="Delivery Restaurant",
            description="Testing delivery status",
            address="Dhaka",
            category="Fast Food",
            price_range="৳৳",
            delivery_available=True,
            latitude=23.8103,
            longitude=90.4125
        )

    def create_rider(self):
        if not model_exists("Rider"):
            return None

        Rider = get_model("Rider")
        field_names = [field.name for field in Rider._meta.fields]

        rider_fields = {}

        if "user" in field_names:
            rider_fields["user"] = self.rider_user

        if "name" in field_names:
            rider_fields["name"] = "Test Rider"

        if "phone" in field_names:
            rider_fields["phone"] = "01700000000"

        if "is_available" in field_names:
            rider_fields["is_available"] = True

        return Rider.objects.create(**rider_fields)

    def test_rider_model_creation(self):
        if not model_exists("Rider"):
            self.skipTest("Rider model not found.")

        rider = self.create_rider()

        self.assertIsNotNone(rider)

        if hasattr(rider, "user"):
            self.assertEqual(rider.user, self.rider_user)

    def test_order_can_have_rider_assigned(self):
        required_models = ["Restaurant", "Order"]

        for model_name in required_models:
            if not model_exists(model_name):
                self.skipTest(f"{model_name} model not found.")

        Order = get_model("Order")
        restaurant = self.create_restaurant()
        rider = self.create_rider()

        order_fields = {
            "customer": self.customer,
            "restaurant": restaurant,
            "status": "confirmed",
            "total_amount": Decimal("500.00"),
            "original_amount": Decimal("500.00"),
            "discount_amount": Decimal("0.00"),
            "applied_deal_title": ""
        }

        order_field_names = [field.name for field in Order._meta.fields]

        if "rider" in order_field_names and rider is not None:
            order_fields["rider"] = rider

        order = Order.objects.create(**order_fields)

        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.restaurant, restaurant)

        if hasattr(order, "rider") and rider is not None:
            self.assertEqual(order.rider, rider)

    def test_delivery_status_update_logic(self):
        if not model_exists("Restaurant") or not model_exists("Order"):
            self.skipTest("Restaurant or Order model not found.")

        Order = get_model("Order")
        restaurant = self.create_restaurant()
        rider = self.create_rider()

        order_fields = {
            "customer": self.customer,
            "restaurant": restaurant,
            "status": "confirmed",
            "total_amount": Decimal("700.00"),
            "original_amount": Decimal("700.00"),
            "discount_amount": Decimal("0.00"),
            "applied_deal_title": ""
        }

        order_field_names = [field.name for field in Order._meta.fields]

        if "rider" in order_field_names and rider is not None:
            order_fields["rider"] = rider

        order = Order.objects.create(**order_fields)

        possible_statuses = [
            "confirmed",
            "assigned",
            "picked_up",
            "on_the_way",
            "delivered"
        ]

        order.status = possible_statuses[-1]
        order.save()

        updated_order = Order.objects.get(id=order.id)

        self.assertEqual(updated_order.status, "delivered")

    def test_rider_dashboard_page_or_api_exists(self):
        possible_paths = [
            "/rider-dashboard/",
            "/rider/dashboard/",
            "/api/rider-dashboard",
            "/api/rider/orders",
        ]

        found = False

        for path in possible_paths:
            response = self.client.get(path)

            if response.status_code == 404 and not path.endswith("/"):
                response = self.client.get(path + "/")

            if response.status_code != 404:
                found = True
                self.assertIn(response.status_code, [200, 302, 400, 401, 403])
                break

        self.assertTrue(
            found,
            "No rider dashboard/API route found. Check urls.py route name."
        )