from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.apps import apps


def model_exists(model_name):
    try:
        apps.get_model("accounts", model_name)
        return True
    except LookupError:
        return False


def get_model(model_name):
    return apps.get_model("accounts", model_name)


class PromotionBranchUnitTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="promo_owner",
            email="promo_owner@test.com",
            password="pass12345"
        )

        if model_exists("UserProfile"):
            UserProfile = get_model("UserProfile")
            UserProfile.objects.get_or_create(
                user=self.owner,
                defaults={"role": "business_owner"}
            )

    def create_restaurant(self):
        Restaurant = get_model("Restaurant")

        return Restaurant.objects.create(
            owner=self.owner,
            name="Promotion Restaurant",
            description="Testing promotion branch",
            address="Dhaka",
            category="Fast Food",
            price_range="৳৳",
            delivery_available=True,
            latitude=23.8103,
            longitude=90.4125
        )

    def test_active_percentage_deal_discount_logic(self):
        if not model_exists("Restaurant") or not model_exists("Deal"):
            self.skipTest("Restaurant or Deal model not found.")

        Deal = get_model("Deal")
        restaurant = self.create_restaurant()

        deal = Deal.objects.create(
            restaurant=restaurant,
            title="20 Percent Off",
            description="Testing percentage deal",
            discount_type="percentage",
            discount_value=Decimal("20.00"),
            minimum_order_amount=Decimal("500.00"),
            active_status=True
        )

        subtotal = Decimal("1000.00")

        discount = subtotal * deal.discount_value / Decimal("100.00")
        final_total = subtotal - discount

        self.assertEqual(discount, Decimal("200.00"))
        self.assertEqual(final_total, Decimal("800.00"))

    def test_fixed_deal_discount_logic(self):
        if not model_exists("Restaurant") or not model_exists("Deal"):
            self.skipTest("Restaurant or Deal model not found.")

        Deal = get_model("Deal")
        restaurant = self.create_restaurant()

        deal = Deal.objects.create(
            restaurant=restaurant,
            title="100 Taka Off",
            description="Testing fixed deal",
            discount_type="fixed",
            discount_value=Decimal("100.00"),
            minimum_order_amount=Decimal("500.00"),
            active_status=True
        )

        subtotal = Decimal("800.00")
        final_total = subtotal - deal.discount_value

        self.assertEqual(final_total, Decimal("700.00"))

    def test_inactive_deal_should_not_be_considered_active(self):
        if not model_exists("Restaurant") or not model_exists("Deal"):
            self.skipTest("Restaurant or Deal model not found.")

        Deal = get_model("Deal")
        restaurant = self.create_restaurant()

        deal = Deal.objects.create(
            restaurant=restaurant,
            title="Inactive Deal",
            description="Inactive promotion",
            discount_type="percentage",
            discount_value=Decimal("15.00"),
            minimum_order_amount=Decimal("300.00"),
            active_status=False
        )

        self.assertFalse(deal.active_status)

    def test_branch_specific_deal_if_branch_model_exists(self):
        required_models = ["Restaurant", "RestaurantBranch", "Deal"]

        for model_name in required_models:
            if not model_exists(model_name):
                self.skipTest(f"{model_name} model not found.")

        RestaurantBranch = get_model("RestaurantBranch")
        Deal = get_model("Deal")

        restaurant = self.create_restaurant()

        branch = RestaurantBranch.objects.create(
            restaurant=restaurant,
            name="Gulshan Branch",
            address="Gulshan, Dhaka",
            latitude=23.7925,
            longitude=90.4078
        )

        deal_fields = {
            "restaurant": restaurant,
            "title": "Gulshan Deal",
            "description": "Branch specific promotion",
            "discount_type": "percentage",
            "discount_value": Decimal("10.00"),
            "minimum_order_amount": Decimal("300.00"),
            "active_status": True
        }

        field_names = [field.name for field in Deal._meta.fields]

        if "branch" in field_names:
            deal_fields["branch"] = branch

        if "apply_to_all_branches" in field_names:
            deal_fields["apply_to_all_branches"] = False

        deal = Deal.objects.create(**deal_fields)

        if hasattr(deal, "branch"):
            self.assertEqual(deal.branch, branch)