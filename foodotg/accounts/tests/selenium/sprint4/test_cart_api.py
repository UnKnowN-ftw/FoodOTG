from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import UserProfile, Restaurant, MenuItem

class CartTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="test@test.com",
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

        self.item = MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Burger",
            price=100
        )

    def test_add_cart(self):
        response = self.client.post(
            "/api/cart/add/",
            {"menu_item_id": self.item.id, "quantity": 1},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access}"
        )

        self.assertEqual(response.status_code, 200)