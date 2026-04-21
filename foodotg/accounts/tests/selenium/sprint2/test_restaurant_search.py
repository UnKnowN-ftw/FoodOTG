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

    def test_dashboard_returns_restaurants_for_authenticated_user(self):
        response = self.client.get(
            "/api/dashboard/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("businesses", response.data)
        self.assertEqual(len(response.data["businesses"]), 2)

        restaurant_names = [restaurant["name"] for restaurant in response.data["businesses"]]
        self.assertIn("Spicy House", restaurant_names)
        self.assertIn("BBQ King", restaurant_names)

    def test_dashboard_contains_restaurant_name_data(self):
        response = self.client.get(
            "/api/dashboard/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        self.assertEqual(response.status_code, 200)

        restaurant_names = [restaurant["name"] for restaurant in response.data["businesses"]]
        self.assertIn("Spicy House", restaurant_names)

    def test_dashboard_contains_restaurant_category_data(self):
        response = self.client.get(
            "/api/dashboard/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        self.assertEqual(response.status_code, 200)

        restaurant_categories = [restaurant["category"] for restaurant in response.data["businesses"]]
        self.assertIn("BBQ", restaurant_categories)

    def test_dashboard_contains_restaurant_location_data(self):
        response = self.client.get(
            "/api/dashboard/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        self.assertEqual(response.status_code, 200)

        restaurant_addresses = [restaurant["address"] for restaurant in response.data["businesses"]]
        self.assertIn("Dhaka", restaurant_addresses)

    def test_dashboard_requires_authentication(self):
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, 401)