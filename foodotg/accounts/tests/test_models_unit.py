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


class FoodOTGModelUnitTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer1",
            email="customer1@test.com",
            password="pass12345"
        )

        self.owner = User.objects.create_user(
            username="owner1",
            email="owner1@test.com",
            password="pass12345"
        )

    def test_user_profile_created_or_can_be_created(self):
        if not model_exists("UserProfile"):
            self.skipTest("UserProfile model not found.")

        UserProfile = get_model("UserProfile")

        profile, created = UserProfile.objects.get_or_create(
            user=self.customer,
            defaults={"role": "customer"}
        )

        self.assertEqual(profile.user.username, "customer1")
        self.assertTrue(hasattr(profile, "role"))

    def test_restaurant_creation(self):
        if not model_exists("Restaurant"):
            self.skipTest("Restaurant model not found.")

        Restaurant = get_model("Restaurant")

        restaurant = Restaurant.objects.create(
            owner=self.owner,
            name="Test Restaurant",
            description="Test description",
            address="Dhaka",
            category="Fast Food",
            price_range="৳৳",
            delivery_available=True,
            latitude=23.8103,
            longitude=90.4125
        )

        self.assertEqual(restaurant.name, "Test Restaurant")
        self.assertEqual(restaurant.owner, self.owner)

    def test_restaurant_branch_creation_if_available(self):
        if not model_exists("Restaurant") or not model_exists("RestaurantBranch"):
            self.skipTest("Restaurant or RestaurantBranch model not found.")

        Restaurant = get_model("Restaurant")
        RestaurantBranch = get_model("RestaurantBranch")

        restaurant = Restaurant.objects.create(
            owner=self.owner,
            name="Main Restaurant",
            description="Main branch test",
            address="Dhaka",
            category="Burger",
            price_range="৳৳",
            delivery_available=True,
            latitude=23.8103,
            longitude=90.4125
        )

        branch = RestaurantBranch.objects.create(
            restaurant=restaurant,
            name="Dhanmondi Branch",
            address="Dhanmondi, Dhaka",
            latitude=23.7465,
            longitude=90.3760
        )

        self.assertEqual(branch.restaurant, restaurant)
        self.assertEqual(branch.name, "Dhanmondi Branch")

    def test_menu_item_creation(self):
        if not model_exists("Restaurant") or not model_exists("MenuItem"):
            self.skipTest("Restaurant or MenuItem model not found.")

        Restaurant = get_model("Restaurant")
        MenuItem = get_model("MenuItem")

        restaurant = Restaurant.objects.create(
            owner=self.owner,
            name="Menu Test Restaurant",
            description="Testing menu",
            address="Dhaka",
            category="Pizza",
            price_range="৳৳",
            delivery_available=True,
            latitude=23.8103,
            longitude=90.4125
        )

        item = MenuItem.objects.create(
            restaurant=restaurant,
            name="Chicken Pizza",
            description="Large pizza",
            price=Decimal("450.00"),
            available=True
        )

        self.assertEqual(item.restaurant, restaurant)
        self.assertEqual(item.price, Decimal("450.00"))
        self.assertTrue(item.available)

    def test_deal_creation(self):
        if not model_exists("Restaurant") or not model_exists("Deal"):
            self.skipTest("Restaurant or Deal model not found.")

        Restaurant = get_model("Restaurant")
        Deal = get_model("Deal")

        restaurant = Restaurant.objects.create(
            owner=self.owner,
            name="Deal Test Restaurant",
            description="Testing deal",
            address="Dhaka",
            category="Rice",
            price_range="৳৳",
            delivery_available=True,
            latitude=23.8103,
            longitude=90.4125
        )

        deal = Deal.objects.create(
            restaurant=restaurant,
            title="10% Off",
            description="Discount for testing",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            minimum_order_amount=Decimal("200.00"),
            active_status=True
        )

        self.assertEqual(deal.restaurant, restaurant)
        self.assertEqual(deal.discount_type, "percentage")
        self.assertTrue(deal.active_status)

    def test_order_creation_if_model_available(self):
        required_models = ["Restaurant", "Order"]

        for model_name in required_models:
            if not model_exists(model_name):
                self.skipTest(f"{model_name} model not found.")

        Restaurant = get_model("Restaurant")
        Order = get_model("Order")

        restaurant = Restaurant.objects.create(
            owner=self.owner,
            name="Order Test Restaurant",
            description="Testing order",
            address="Dhaka",
            category="Kacchi",
            price_range="৳৳৳",
            delivery_available=True,
            latitude=23.8103,
            longitude=90.4125
        )

        order = Order.objects.create(
            customer=self.customer,
            restaurant=restaurant,
            status="confirmed",
            total_amount=Decimal("500.00"),
            original_amount=Decimal("500.00"),
            discount_amount=Decimal("0.00"),
            applied_deal_title=""
        )

        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.restaurant, restaurant)
        self.assertEqual(order.total_amount, Decimal("500.00"))