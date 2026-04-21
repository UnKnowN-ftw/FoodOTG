from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import UserProfile, Restaurant, Order


class OrderConfirmationPageTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="confirm@test.com",
            password="12345678"
        )
        UserProfile.objects.create(user=self.user, role="customer")

        self.restaurant = Restaurant.objects.create(
            owner=self.user,
            name="Confirm Test Restaurant",
            description="Food",
            address="Dhaka",
            category="BBQ",
            price_range="৳৳"
        )

        self.order = Order.objects.create(
            customer=self.user,
            restaurant=self.restaurant,
            total_amount=200,
            status="confirmed"
        )

    def test_order_confirmation_page_loads(self):
        response = self.client.get(f"/order-confirmation/{self.order.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Order Confirmed")