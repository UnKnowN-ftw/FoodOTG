from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Preference, UserProfile


class CustomerPreferencesTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="prefuser@example.com",
            email="prefuser@example.com",
            password="testpass123"
        )
        UserProfile.objects.create(user=self.user, role="customer")

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_save_preferences_success(self):
        response = self.client.post(
            "/api/save-preferences/",
            {
                "preferences": ["Chinese", "BBQ"],
                "budget_range": "৳৳"
            },
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Preferences saved successfully")

        pref = Preference.objects.get(user=self.user)
        self.assertEqual(pref.taste_preferences, ["Chinese", "BBQ"])
        self.assertEqual(pref.budget_range, "৳৳")

    def test_save_preferences_requires_authentication(self):
        response = self.client.post(
            "/api/save-preferences/",
            {
                "preferences": ["Fast Food"],
                "budget_range": "৳"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 401)