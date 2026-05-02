from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import UserProfile, Restaurant, Order

class ReviewTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="review@test.com",
            password="12345678"
        )
        UserProfile.objects.create(user=self.user, role="customer")

        token = RefreshToken.for_user(self.user)
        self.access = str(token.access_token)

        self.restaurant = Restaurant.objects.create(
            owner=self.user,
            name="Test",
            description="Food",
            address="Dhaka",
            category="BBQ",
            price_range="৳৳"
        )

        self.order = Order.objects.create(
            customer=self.user,
            restaurant=self.restaurant,
            total_amount=100,
            status="completed"   # 🔥 FIX
        )

    def test_review(self):
        response = self.client.post(
            f"/api/orders/{self.order.id}/review/",
            {"rating": 5, "comment": "Good"},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access}"
        )

        self.assertEqual(response.status_code, 201)