from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Restaurant, Deal, UserProfile


class PromotionTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="promo@example.com",
            email="promo@example.com",
            password="testpass123"
        )
        UserProfile.objects.create(user=self.user, role="business_owner")

        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)

        self.restaurant = Restaurant.objects.create(
            owner=self.user,
            name="Promo Test",
            description="Deals",
            address="Dhaka",
            category="Fusion",
            price_range="৳৳"
        )

def test_add_promotion(self):
    response = self.client.post(
        f"/api/restaurants/{self.restaurant.id}/promotions/add/",
        {
            "title": "50% OFF",
            "description": "Big discount",
            "active_status": True
        },
        format="json",
        HTTP_AUTHORIZATION=f"Bearer {self.token}"
    )

    print("STATUS:", response.status_code)
    print("DATA:", response.data)

    self.assertEqual(response.status_code, 201)
    self.assertEqual(Deal.objects.count(), 1)
    
    def test_delete_promotion(self):
        deal = Deal.objects.create(
            restaurant=self.restaurant,
            title="Test Deal",
            description="Desc",
            active_status=True
        )

        response = self.client.delete(
            f"/api/promotions/{deal.id}/delete/",
            HTTP_AUTHORIZATION=f"Bearer {self.token}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Deal.objects.count(), 0)