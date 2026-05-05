import re

from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Rider
from .models import (
    Cart,
    CartItem,
    Deal,
    MenuItem,
    Order,
    OrderItem,
    Preference,
    Restaurant,
    Review,
    UserProfile,
)


class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(
    choices=[
        ("customer", "Customer"),
        ("business_owner", "Business Owner"),
        ("admin", "Admin"),
        ("rider", "Rider"),]
    )

    class Meta:
        model = User
        fields = ["name", "email", "password", "role"]
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
        }

    def validate_email(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Security requires 6+ characters.")
        if not re.search(r"[A-Za-z]", value) or not re.search(r"[0-9]", value):
            raise serializers.ValidationError("Password must contain both letters and numbers.")
        return value

    def create(self, validated_data):
        role = validated_data.pop("role")

        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["name"],
        )

        UserProfile.objects.create(user=user, role=role)
        return user


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = "__all__"
        read_only_fields = ["owner", "average_rating", "created_at"]

def create(self, validated_data):
    role = validated_data.pop("role", "customer")

    user = User.objects.create_user(
        username=validated_data["username"],
        email=validated_data.get("email"),
        password=validated_data["password"],
        first_name=validated_data.get("first_name", "")
    )

    # create user profile
    UserProfile.objects.create(user=user, role=role)


    if role == "rider":
        Rider.objects.create(user=user)

    return user


class DealSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)

    class Meta:
        model = Deal
        fields = [
            "id",
            "restaurant",
            "restaurant_name",
            "title",
            "description",
            "active_status",
            "discount_type",
            "discount_value",
            "minimum_order_amount",
        ]
        read_only_fields = ["restaurant_name"]


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = ["id", "user", "budget_range", "taste_preferences"]


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = "__all__"
        read_only_fields = ["restaurant", "created_at"]


class CartItemSerializer(serializers.ModelSerializer):
    menu_item_id = serializers.IntegerField(source="menu_item.id", read_only=True)
    menu_item_name = serializers.CharField(source="menu_item.name", read_only=True)
    restaurant_id = serializers.IntegerField(source="menu_item.restaurant.id", read_only=True)
    restaurant_name = serializers.CharField(source="menu_item.restaurant.name", read_only=True)
    price = serializers.DecimalField(
        source="menu_item.price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    available = serializers.BooleanField(source="menu_item.available", read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "menu_item_id",
            "menu_item_name",
            "restaurant_id",
            "restaurant_name",
            "price",
            "available",
            "quantity",
            "subtotal",
        ]

    def get_subtotal(self, obj):
        return obj.subtotal


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "items", "total_items", "total_price", "updated_at"]

    def get_total_items(self, obj):
        return obj.total_items

    def get_total_price(self, obj):
        return obj.total_price


class OrderItemSerializer(serializers.ModelSerializer):
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "item_name", "unit_price", "quantity", "subtotal"]

    def get_subtotal(self, obj):
        return obj.subtotal


class ReviewSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "order",
            "restaurant",
            "restaurant_name",
            "rating",
            "comment",
            "is_approved",
            "created_at",
        ]
        read_only_fields = [
            "order",
            "restaurant",
            "restaurant_name",
            "is_approved",
            "created_at",
        ]


class OrderSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    rider_name = serializers.CharField(source="rider.user.username", read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    review_submitted = serializers.SerializerMethodField()
    review = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "restaurant",
            "restaurant_name",
            "rider",
            "rider_name",

            "customer_name",
            "phone_number",
            "delivery_address",
            "payment_method",
            "delivery_charge",

            "status",
            "original_amount",
            "discount_amount",
            "total_amount",
            "applied_deal_title",
            "created_at",
            "items",
            "review_submitted",
            "review",
        ]

    def get_review_submitted(self, obj):
        return hasattr(obj, "review")

    def get_review(self, obj):
        if hasattr(obj, "review"):
            return {
                "id": obj.review.id,
                "rating": obj.review.rating,
                "comment": obj.review.comment,
                "created_at": obj.review.created_at,
            }
        return None
choices=[
    ("customer", "Customer"),
    ("business_owner", "Business Owner"),
    ("admin", "Admin"),
    ("rider", "Rider"),
]


