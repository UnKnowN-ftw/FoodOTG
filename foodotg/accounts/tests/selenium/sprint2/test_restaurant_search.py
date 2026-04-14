from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Restaurant, UserProfile


class RestaurantSearchTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="searchuser@example.com",
            email="searchuser@example.com",
            password="testpass123"
        )
        UserProfile.objects.create(user=self.user, role="customer")

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        Restaurant.objects.create(
            owner=self.user,
            name="Spicy House",
            description="Hot and spicy food",
            address="Dhaka",
            category="Chinese",
            price_range="৳৳"
        )

        Restaurant.objects.create(
            owner=self.user,
            name="BBQ King",
            description="Best BBQ in town",
            address="Chittagong",
            category="BBQ",
            price_range="৳৳৳"
        )

    def test_search_restaurants_by_name(self):
        response = self.client.get(
            "/api/search-restaurants/?q=Spicy",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Spicy House")

    def test_search_restaurants_by_category(self):
        response = self.client.get(
            "/api/search-restaurants/?category=BBQ",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "BBQ King")

    def test_search_restaurants_by_location(self):
        response = self.client.get(
            "/api/search-restaurants/?location=Dhaka",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Spicy House")

    def test_search_restaurants_requires_authentication(self):
        response = self.client.get("/api/search-restaurants/?q=Spicy")
        self.assertEqual(response.status_code, 401)