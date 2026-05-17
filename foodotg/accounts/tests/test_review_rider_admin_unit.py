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


class FoodOTGReviewRiderAdminUnitTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="reviewcustomer",
            email="reviewcustomer@test.com",
            password="pass12345"
        )

        self.owner = User.objects.create_user(
            username="reviewowner",
            email="reviewowner@test.com",
            password="pass12345"
        )

        self.admin_user = User.objects.create_superuser(
            username="adminuser",
            email="admin@test.com",
            password="adminpass123"
        )

        if model_exists("UserProfile"):
            UserProfile = get_model("UserProfile")

            UserProfile.objects.get_or_create(
                user=self.customer,
                defaults={"role": "customer"}
            )

            UserProfile.objects.get_or_create(
                user=self.owner,
                defaults={"role": "business_owner"}
            )

            UserProfile.objects.get_or_create(
                user=self.admin_user,
                defaults={"role": "admin"}
            )

    def get_field_names(self, model_class):
        return [field.name for field in model_class._meta.fields]

    def create_restaurant(self):
        Restaurant = get_model("Restaurant")

        return Restaurant.objects.create(
            owner=self.owner,
            name="Review Restaurant",
            description="Testing review",
            address="Dhaka",
            category="Food",
            price_range="৳৳",
            delivery_available=True,
            latitude=23.8103,
            longitude=90.4125
        )

    def create_rider(self):
        if not model_exists("Rider"):
            return None

        Rider = get_model("Rider")
        field_names = self.get_field_names(Rider)

        rider_user = User.objects.create_user(
            username="rideruser",
            email="rider@test.com",
            password="pass12345"
        )

        rider_fields = {}

        if "user" in field_names:
            rider_fields["user"] = rider_user

        if "name" in field_names:
            rider_fields["name"] = "Test Rider"

        if "phone" in field_names:
            rider_fields["phone"] = "01700000000"

        if "is_available" in field_names:
            rider_fields["is_available"] = True

        return Rider.objects.create(**rider_fields)

    def create_order(self, restaurant, rider=None):
        if not model_exists("Order"):
            return None

        Order = get_model("Order")
        field_names = self.get_field_names(Order)

        order_fields = {}

        if "customer" in field_names:
            order_fields["customer"] = self.customer

        if "user" in field_names:
            order_fields["user"] = self.customer

        if "restaurant" in field_names:
            order_fields["restaurant"] = restaurant

        if "rider" in field_names and rider is not None:
            order_fields["rider"] = rider

        if "status" in field_names:
            order_fields["status"] = "delivered"

        if "total_amount" in field_names:
            order_fields["total_amount"] = Decimal("600.00")

        if "original_amount" in field_names:
            order_fields["original_amount"] = Decimal("600.00")

        if "discount_amount" in field_names:
            order_fields["discount_amount"] = Decimal("0.00")

        if "applied_deal_title" in field_names:
            order_fields["applied_deal_title"] = ""

        return Order.objects.create(**order_fields)

    def create_review(self, restaurant, rating=5, comment="Good food"):
        if not model_exists("Review"):
            return None

        Review = get_model("Review")
        review_field_names = self.get_field_names(Review)

        order = self.create_order(restaurant)

        review_fields = {}

        if "restaurant" in review_field_names:
            review_fields["restaurant"] = restaurant

        if "order" in review_field_names:
            if order is None:
                self.skipTest("Review requires order but Order model not found.")
            review_fields["order"] = order

        if "customer" in review_field_names:
            review_fields["customer"] = self.customer

        if "user" in review_field_names:
            review_fields["user"] = self.customer

        if "rating" in review_field_names:
            review_fields["rating"] = rating

        if "comment" in review_field_names:
            review_fields["comment"] = comment

        if "review" in review_field_names:
            review_fields["review"] = comment

        if "is_approved" in review_field_names:
            review_fields["is_approved"] = True

        if "status" in review_field_names:
            review_fields["status"] = "approved"

        return Review.objects.create(**review_fields)

    def test_review_model_if_available(self):
        if not model_exists("Restaurant") or not model_exists("Review"):
            self.skipTest("Restaurant or Review model not found.")

        restaurant = self.create_restaurant()
        review = self.create_review(
            restaurant=restaurant,
            rating=5,
            comment="Good food"
        )

        self.assertIsNotNone(review)

        if hasattr(review, "restaurant"):
            self.assertEqual(review.restaurant, restaurant)

        if hasattr(review, "user"):
            self.assertEqual(review.user, self.customer)

        if hasattr(review, "customer"):
            self.assertEqual(review.customer, self.customer)

        if hasattr(review, "rating"):
            self.assertEqual(review.rating, 5)

        if hasattr(review, "order"):
            self.assertIsNotNone(review.order)

    def test_review_report_model_if_available(self):
        required_models = ["Restaurant", "Review", "ReviewReport"]

        for model_name in required_models:
            if not model_exists(model_name):
                self.skipTest(f"{model_name} model not found.")

        ReviewReport = get_model("ReviewReport")

        restaurant = self.create_restaurant()
        review = self.create_review(
            restaurant=restaurant,
            rating=2,
            comment="Fake review test"
        )

        report_field_names = self.get_field_names(ReviewReport)

        report_fields = {}

        if "review" in report_field_names:
            report_fields["review"] = review

        if "reason" in report_field_names:
            report_fields["reason"] = "Fake review"

        if "reported_by" in report_field_names:
            report_fields["reported_by"] = self.owner

        if "user" in report_field_names:
            report_fields["user"] = self.owner

        if "reporter" in report_field_names:
            report_fields["reporter"] = self.owner

        if "status" in report_field_names:
            report_fields["status"] = "pending"

        report = ReviewReport.objects.create(**report_fields)

        if hasattr(report, "review"):
            self.assertEqual(report.review, review)

    def test_rider_model_if_available(self):
        if not model_exists("Rider"):
            self.skipTest("Rider model not found.")

        rider = self.create_rider()

        self.assertIsNotNone(rider)

        if hasattr(rider, "user"):
            self.assertEqual(rider.user.username, "rideruser")

    def test_assign_rider_to_order_if_available(self):
        required_models = ["Restaurant", "Order", "Rider"]

        for model_name in required_models:
            if not model_exists(model_name):
                self.skipTest(f"{model_name} model not found.")

        restaurant = self.create_restaurant()
        rider = self.create_rider()
        order = self.create_order(restaurant=restaurant, rider=rider)

        self.assertIsNotNone(order)

        if hasattr(order, "rider") and rider is not None:
            self.assertEqual(order.rider, rider)

        if hasattr(order, "status"):
            self.assertEqual(order.status, "delivered")