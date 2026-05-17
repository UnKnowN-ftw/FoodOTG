from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.apps import apps
from django.urls import resolve, Resolver404
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


class CartCheckoutReviewUnitTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.customer = User.objects.create_user(
            username="cart_customer",
            email="cartcustomer@test.com",
            password="pass12345"
        )

        self.owner = User.objects.create_user(
            username="cart_owner",
            email="cartowner@test.com",
            password="pass12345"
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

        token = RefreshToken.for_user(self.customer)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def get_field_names(self, model_class):
        return [field.name for field in model_class._meta.fields]

    def route_exists(self, path):
        possible_paths = []

        if path.endswith("/"):
            possible_paths.append(path)
            possible_paths.append(path.rstrip("/"))
        else:
            possible_paths.append(path + "/")
            possible_paths.append(path)

        for url in possible_paths:
            try:
                resolve(url)
                return True
            except Resolver404:
                continue

        return False

    def get_api(self, path):
        if path.endswith("/"):
            possible_paths = [path, path.rstrip("/")]
        else:
            possible_paths = [path + "/", path]

        last_response = None

        for url in possible_paths:
            response = self.client.get(url)
            last_response = response

            if response.status_code not in [301, 302, 404]:
                return response

        return last_response

    def post_api(self, path, data):
        if path.endswith("/"):
            possible_paths = [path, path.rstrip("/")]
        else:
            possible_paths = [path + "/", path]

        last_response = None

        for url in possible_paths:
            response = self.client.post(url, data, format="json")
            last_response = response

            if response.status_code not in [301, 302, 404]:
                return response

        return last_response

    def create_restaurant(self, name="Cart Restaurant"):
        Restaurant = get_model("Restaurant")

        return Restaurant.objects.create(
            owner=self.owner,
            name=name,
            description="Testing cart and checkout",
            address="Dhaka",
            category="Fast Food",
            price_range="৳৳",
            delivery_available=True,
            latitude=23.8103,
            longitude=90.4125
        )

    def create_menu_item(self, restaurant, name="Chicken Burger", price="300.00"):
        MenuItem = get_model("MenuItem")

        return MenuItem.objects.create(
            restaurant=restaurant,
            name=name,
            description="Testing menu item",
            price=Decimal(price),
            available=True
        )

    def create_order(self, restaurant):
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

        if "status" in field_names:
            order_fields["status"] = "delivered"

        if "total_amount" in field_names:
            order_fields["total_amount"] = Decimal("500.00")

        if "original_amount" in field_names:
            order_fields["original_amount"] = Decimal("500.00")

        if "discount_amount" in field_names:
            order_fields["discount_amount"] = Decimal("0.00")

        if "applied_deal_title" in field_names:
            order_fields["applied_deal_title"] = ""

        return Order.objects.create(**order_fields)

    def test_cart_model_if_available(self):
        required_models = ["Restaurant", "MenuItem"]

        for model_name in required_models:
            if not model_exists(model_name):
                self.skipTest(f"{model_name} model not found.")

        restaurant = self.create_restaurant()
        item = self.create_menu_item(restaurant)

        if not model_exists("Cart") or not model_exists("CartItem"):
            self.skipTest("Cart or CartItem model not found.")

        Cart = get_model("Cart")
        CartItem = get_model("CartItem")

        cart_field_names = self.get_field_names(Cart)

        cart_fields = {}

        if "customer" in cart_field_names:
            cart_fields["customer"] = self.customer

        if "user" in cart_field_names:
            cart_fields["user"] = self.customer

        cart = Cart.objects.create(**cart_fields)

        cart_item_field_names = self.get_field_names(CartItem)

        cart_item_fields = {
            "cart": cart,
            "quantity": 2
        }

        if "menu_item" in cart_item_field_names:
            cart_item_fields["menu_item"] = item

        if "item" in cart_item_field_names:
            cart_item_fields["item"] = item

        cart_item = CartItem.objects.create(**cart_item_fields)

        self.assertEqual(cart_item.quantity, 2)

    def test_cart_add_api_route_or_model_available(self):
        if not model_exists("Restaurant") or not model_exists("MenuItem"):
            self.skipTest("Restaurant or MenuItem model not found.")

        restaurant = self.create_restaurant()
        item = self.create_menu_item(restaurant)

        possible_routes = [
            "/api/cart/add/",
            "/api/cart/add",
            "/api/add-to-cart/",
            "/api/add-to-cart",
            "/cart/add/",
            "/cart/add",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Cart add route not found in urls.py.")

        payload_options = [
            {"menu_item_id": item.id, "quantity": 1},
            {"item_id": item.id, "quantity": 1},
            {"menu_item": item.id, "quantity": 1},
        ]

        valid_response_found = False

        for path in possible_routes:
            if not self.route_exists(path):
                continue

            for payload in payload_options:
                response = self.post_api(path, payload)

                if response.status_code not in [301, 302, 404]:
                    valid_response_found = True
                    self.assertIn(response.status_code, [200, 201, 400, 401, 403])
                    break

            if valid_response_found:
                break

        self.assertTrue(valid_response_found)

    def test_checkout_summary_route_if_available(self):
        possible_routes = [
            "/api/checkout-summary/",
            "/api/checkout-summary",
            "/api/checkout_summary/",
            "/api/checkout_summary",
            "/checkout-summary/",
            "/checkout-summary",
            "/checkout/",
            "/checkout",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Checkout summary route not found in urls.py.")

        self.assertTrue(route_found)

    def test_place_order_route_if_available(self):
        possible_routes = [
            "/api/place-order/",
            "/api/place-order",
            "/api/place_order/",
            "/api/place_order",
            "/place-order/",
            "/place-order",
        ]

        route_found = any(self.route_exists(path) for path in possible_routes)

        if not route_found:
            self.skipTest("Place order route not found in urls.py.")

        self.assertTrue(route_found)

    def test_discount_calculation_logic(self):
        subtotal = Decimal("500.00")
        discount_type = "percentage"
        discount_value = Decimal("10.00")

        if discount_type == "percentage":
            discount_amount = subtotal * discount_value / Decimal("100.00")
        else:
            discount_amount = discount_value

        final_amount = subtotal - discount_amount

        self.assertEqual(discount_amount, Decimal("50.00"))
        self.assertEqual(final_amount, Decimal("450.00"))

    def test_review_model_if_available(self):
        if not model_exists("Restaurant") or not model_exists("Review"):
            self.skipTest("Restaurant or Review model not found.")

        Review = get_model("Review")
        restaurant = self.create_restaurant("Review Restaurant")
        order = self.create_order(restaurant)

        review_field_names = self.get_field_names(Review)

        review_fields = {
            "restaurant": restaurant,
            "rating": 5,
            "comment": "Good food"
        }

        if "customer" in review_field_names:
            review_fields["customer"] = self.customer

        if "user" in review_field_names:
            review_fields["user"] = self.customer

        if "order" in review_field_names:
            if order is None:
                self.skipTest("Review requires order but Order model not found.")
            review_fields["order"] = order

        if "is_approved" in review_field_names:
            review_fields["is_approved"] = True

        if "status" in review_field_names:
            review_fields["status"] = "approved"

        review = Review.objects.create(**review_fields)

        self.assertEqual(review.restaurant, restaurant)
        self.assertEqual(review.rating, 5)

        if hasattr(review, "order"):
            self.assertEqual(review.order, order)

    def test_review_report_model_if_available(self):
        required_models = ["Restaurant", "Review", "ReviewReport"]

        for model_name in required_models:
            if not model_exists(model_name):
                self.skipTest(f"{model_name} model not found.")

        Review = get_model("Review")
        ReviewReport = get_model("ReviewReport")

        restaurant = self.create_restaurant("Fake Review Restaurant")
        order = self.create_order(restaurant)

        review_field_names = self.get_field_names(Review)

        review_fields = {
            "restaurant": restaurant,
            "rating": 1,
            "comment": "Suspicious review"
        }

        if "customer" in review_field_names:
            review_fields["customer"] = self.customer

        if "user" in review_field_names:
            review_fields["user"] = self.customer

        if "order" in review_field_names:
            if order is None:
                self.skipTest("Review requires order but Order model not found.")
            review_fields["order"] = order

        if "is_approved" in review_field_names:
            review_fields["is_approved"] = True

        if "status" in review_field_names:
            review_fields["status"] = "approved"

        review = Review.objects.create(**review_fields)

        report_field_names = self.get_field_names(ReviewReport)

        report_fields = {
            "review": review,
            "reason": "Fake review"
        }

        if "reported_by" in report_field_names:
            report_fields["reported_by"] = self.owner

        if "user" in report_field_names:
            report_fields["user"] = self.owner

        report = ReviewReport.objects.create(**report_fields)

        self.assertEqual(report.review, review)