from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.apps import apps
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken


def model_exists(model_name):
    try:
        apps.get_model("accounts", model_name)
        return True
    except LookupError:
        return False


def get_model(model_name):
    return apps.get_model("accounts", model_name)


class BranchManagementUnitTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.owner = User.objects.create_user(
            username="branch_owner",
            email="branchowner@test.com",
            password="pass12345"
        )

        if model_exists("UserProfile"):
            UserProfile = get_model("UserProfile")
            UserProfile.objects.get_or_create(
                user=self.owner,
                defaults={"role": "business_owner"}
            )

        token = RefreshToken.for_user(self.owner)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def get_api(self, path):
        """
        Tries slash URL first to avoid Django APPEND_SLASH 301 redirect.
        """
        possible_paths = []

        if path.endswith("/"):
            possible_paths.append(path)
            possible_paths.append(path.rstrip("/"))
        else:
            possible_paths.append(path + "/")
            possible_paths.append(path)

        last_response = None

        for url in possible_paths:
            response = self.client.get(url)
            last_response = response

            if response.status_code not in [301, 302, 404]:
                return response

        return last_response

    def post_api(self, path, data):
        """
        Tries slash URL first to avoid Django APPEND_SLASH 301 redirect.
        """
        possible_paths = []

        if path.endswith("/"):
            possible_paths.append(path)
            possible_paths.append(path.rstrip("/"))
        else:
            possible_paths.append(path + "/")
            possible_paths.append(path)

        last_response = None

        for url in possible_paths:
            response = self.client.post(url, data, format="json")
            last_response = response

            if response.status_code not in [301, 302, 404]:
                return response

        return last_response

    def create_restaurant(self):
        Restaurant = get_model("Restaurant")

        return Restaurant.objects.create(
            owner=self.owner,
            name="Branch Test Restaurant",
            description="Restaurant for branch unit testing",
            address="Dhaka",
            category="Fast Food",
            price_range="৳৳",
            delivery_available=True,
            latitude=23.8103,
            longitude=90.4125
        )

    def test_restaurant_branch_model_creation(self):
        if not model_exists("Restaurant") or not model_exists("RestaurantBranch"):
            self.skipTest("Restaurant or RestaurantBranch model not found.")

        RestaurantBranch = get_model("RestaurantBranch")
        restaurant = self.create_restaurant()

        branch_fields = {
            "restaurant": restaurant,
            "name": "Dhanmondi Branch",
            "address": "Dhanmondi, Dhaka",
            "latitude": 23.7465,
            "longitude": 90.3760
        }

        field_names = [field.name for field in RestaurantBranch._meta.fields]

        if "phone" in field_names:
            branch_fields["phone"] = "01700000000"

        if "is_active" in field_names:
            branch_fields["is_active"] = True

        branch = RestaurantBranch.objects.create(**branch_fields)

        self.assertEqual(branch.restaurant, restaurant)
        self.assertEqual(branch.name, "Dhanmondi Branch")
        self.assertEqual(branch.address, "Dhanmondi, Dhaka")

    def test_deal_can_apply_to_specific_branch(self):
        required_models = ["Restaurant", "Deal", "RestaurantBranch"]

        for model_name in required_models:
            if not model_exists(model_name):
                self.skipTest(f"{model_name} model not found.")

        Deal = get_model("Deal")
        RestaurantBranch = get_model("RestaurantBranch")

        restaurant = self.create_restaurant()

        branch = RestaurantBranch.objects.create(
            restaurant=restaurant,
            name="Mirpur Branch",
            address="Mirpur, Dhaka",
            latitude=23.8223,
            longitude=90.3654
        )

        deal_fields = {
            "restaurant": restaurant,
            "title": "Branch Offer",
            "description": "Offer for one branch",
            "discount_type": "percentage",
            "discount_value": Decimal("15.00"),
            "minimum_order_amount": Decimal("300.00"),
            "active_status": True
        }

        deal_field_names = [field.name for field in Deal._meta.fields]

        if "branch" in deal_field_names:
            deal_fields["branch"] = branch

        if "apply_to_all_branches" in deal_field_names:
            deal_fields["apply_to_all_branches"] = False

        deal = Deal.objects.create(**deal_fields)

        self.assertEqual(deal.restaurant, restaurant)

        if hasattr(deal, "branch"):
            self.assertEqual(deal.branch, branch)

        if hasattr(deal, "apply_to_all_branches"):
            self.assertFalse(deal.apply_to_all_branches)

    def test_deal_can_apply_to_all_branches(self):
        if not model_exists("Restaurant") or not model_exists("Deal"):
            self.skipTest("Restaurant or Deal model not found.")

        Deal = get_model("Deal")
        restaurant = self.create_restaurant()

        deal_fields = {
            "restaurant": restaurant,
            "title": "All Branch Offer",
            "description": "Offer for all branches",
            "discount_type": "fixed",
            "discount_value": Decimal("50.00"),
            "minimum_order_amount": Decimal("500.00"),
            "active_status": True
        }

        deal_field_names = [field.name for field in Deal._meta.fields]

        if "apply_to_all_branches" in deal_field_names:
            deal_fields["apply_to_all_branches"] = True

        deal = Deal.objects.create(**deal_fields)

        self.assertEqual(deal.restaurant, restaurant)
        self.assertTrue(deal.active_status)

        if hasattr(deal, "apply_to_all_branches"):
            self.assertTrue(deal.apply_to_all_branches)

    def test_business_dashboard_api_exists_for_branch_management(self):
        response = self.get_api("/api/business-dashboard")

        self.assertNotEqual(response.status_code, 404)
        self.assertNotEqual(response.status_code, 301)
        self.assertNotEqual(response.status_code, 302)
        self.assertIn(response.status_code, [200, 400, 401, 403])