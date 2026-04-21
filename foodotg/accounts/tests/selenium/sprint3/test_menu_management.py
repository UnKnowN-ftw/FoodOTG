from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Restaurant, MenuItem, UserProfile


class MenuManagementTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="menuowner@example.com",
            password="testpass123"
        )
        UserProfile.objects.create(user=self.user, role="business_owner")

        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        self.restaurant = Restaurant.objects.create(
            owner=self.user,
            name="Menu Test",
            description="Food",
            address="Dhaka",
            category="BBQ",
            price_range="৳৳"
        )

    def test_add_menu_item(self):
        response = self.client.post(
            f"/api/restaurants/{self.restaurant.id}/menu/add/",
            {
                "name": "Burger",
                "price": 200
            },
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(MenuItem.objects.count(), 1)

    def test_update_menu_item(self):
        item = MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Pizza",
            price=300
        )

        response = self.client.put(
            f"/api/menu-items/{item.id}/update/",
            {"price": 350},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}"
        )

        self.assertEqual(response.status_code, 200)

    def test_delete_menu_item(self):
        item = MenuItem.objects.create(
            restaurant=self.restaurant,
            name="Pasta",
            price=250
        )

        response = self.client.delete(
            f"/api/menu-items/{item.id}/delete/",
            HTTP_AUTHORIZATION=f"Bearer {self.token}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(MenuItem.objects.count(), 0)