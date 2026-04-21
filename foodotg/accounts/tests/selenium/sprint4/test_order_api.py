from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import UserProfile, Restaurant, MenuItem

class OrderTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="order@test.com",
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
            name="Pizza",
            price=200
        )

    def test_full_order_flow(self):

        # add to cart
        self.client.post(
            "/api/cart/add/",
            {"menu_item_id": self.item.id, "quantity": 1},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access}"
        )

        # checkout
        res1 = self.client.get(
            "/api/checkout/summary/",
            HTTP_AUTHORIZATION=f"Bearer {self.access}"
        )
        self.assertEqual(res1.status_code, 200)

        # place order
        res2 = self.client.post(
            "/api/orders/place/",
            HTTP_AUTHORIZATION=f"Bearer {self.access}"
        )

        self.assertEqual(res2.status_code, 201)