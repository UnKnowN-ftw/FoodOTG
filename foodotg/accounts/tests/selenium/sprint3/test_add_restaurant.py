from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Restaurant, UserProfile


class AddRestaurantTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="owner@example.com",
            email="owner@example.com",
            password="testpass123"
        )
        UserProfile.objects.create(user=self.user, role="business_owner")

        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

    def test_add_restaurant_success(self):
        response = self.client.post(
            "/api/add-restaurant/",
            {
                "name": "Test Restaurant",
                "description": "Nice food",
                "address": "Dhaka",
                "category": "Chinese",
                "price_range": "৳৳"
            },
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.token}"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Restaurant.objects.count(), 1)

    def test_add_restaurant_requires_auth(self):
        response = self.client.post("/api/add-restaurant/", {})

        self.assertEqual(response.status_code, 401)