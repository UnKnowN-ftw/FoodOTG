from decimal import Decimal
import uuid

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Avg
from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Rider
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from django.db import models

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
    ReviewReport,
    UserProfile,
)
from .serializers import (
    CartSerializer,
    DealSerializer,
    MenuItemSerializer,
    OrderSerializer,
    RegisterSerializer,
    RestaurantSerializer,
    ReviewSerializer,
)


def is_foodotg_admin(user):
    if not user or not user.is_authenticated:
        return False

    if user.is_staff or user.is_superuser:
        return True

    try:
        return user.userprofile.role == "admin"
    except UserProfile.DoesNotExist:
        return False


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def update_restaurant_average_rating(restaurant):
    avg_rating = (
        Review.objects.filter(restaurant=restaurant, is_approved=True).aggregate(
            avg=Avg("rating")
        )["avg"]
        or 0.0
    )

    restaurant.average_rating = round(float(avg_rating), 1)
    restaurant.save(update_fields=["average_rating"])


@api_view(["POST"])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Registration is Complete"}, status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def user_login(request):
    email = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=email, password=password)

    if user:
        refresh = RefreshToken.for_user(user)

        try:
            role = user.userprofile.role
        except UserProfile.DoesNotExist:
            role = "customer"

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "role": role,
                "message": "Login successful",
            },
            status=status.HTTP_200_OK,
        )

    return Response(
        {"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(["POST"])
def user_logout(request):
    return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_preferences(request):
    preferences = request.data.get("preferences", [])
    budget_range = request.data.get("budget_range", "")

    pref_obj, _ = Preference.objects.get_or_create(user=request.user)
    pref_obj.taste_preferences = preferences
    pref_obj.budget_range = budget_range
    pref_obj.save()

    return Response(
        {
            "message": "Preferences saved successfully",
            "preferences": pref_obj.taste_preferences,
            "budget_range": pref_obj.budget_range,
        }
    )


# =========================
# PAGE VIEWS
# =========================
def login_page(request):
    return render(request, "login.html")


def customer_login_page(request):
    return render(request, "customer_login.html")


def business_login_page(request):
    return render(request, "business_login.html")


def admin_login_page(request):
    return render(request, "admin_login.html")


def register_page(request):
    return render(request, "register.html")


def customer_register_page(request):
    return render(request, "customer_register.html")


def business_register_page(request):
    return render(request, "business_register.html")


def customer_dashboard_page(request):
    return render(request, "customer_dashboard.html")


def business_dashboard_page(request):
    return render(request, "business_dashboard.html")


def checkout_page(request):
    return render(request, "checkout.html")


def order_confirmation_page(request, order_id):
    return render(request, "order_confirmation.html", {"order_id": order_id})


# =========================
# CUSTOMER DASHBOARD DATA
# =========================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    restaurants = Restaurant.objects.all()
    deals = Deal.objects.filter(active_status=True)

    restaurant_data = RestaurantSerializer(restaurants, many=True).data
    deal_data = DealSerializer(deals, many=True).data

    user_preferences = []
    budget_range = ""

    try:
        pref = Preference.objects.get(user=request.user)
        user_preferences = pref.taste_preferences
        budget_range = pref.budget_range or ""
    except Preference.DoesNotExist:
        pass

    return Response(
        {
            "businesses": restaurant_data,
            "deals": deal_data,
            "preferences": user_preferences,
            "budget_range": budget_range,
        }
    )


# =========================
# BUSINESS DASHBOARD DATA
# =========================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_dashboard_data(request):
    restaurants = Restaurant.objects.filter(owner=request.user)
    serializer = RestaurantSerializer(restaurants, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_reviews(request):
    reviews = (
        Review.objects.filter(restaurant__owner=request.user, is_approved=True)
        .select_related("restaurant", "user", "order")
        .order_by("-created_at")
    )

    data = []
    for review in reviews:
        data.append(
            {
                "id": review.id,
                "restaurant_id": review.restaurant.id,
                "restaurant_name": review.restaurant.name,
                "customer_name": review.user.first_name or review.user.username,
                "order_id": review.order.id,
                "rating": review.rating,
                "comment": review.comment,
                "created_at": review.created_at,
            }
        )

    return Response(data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def add_restaurant(request):
    serializer = RestaurantSerializer(data=request.data, context={"request": request})

    if serializer.is_valid():
        serializer.save(owner=request.user)
        return Response(
            {"message": "Restaurant added successfully"}, status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =========================
# BUSINESS MENU MANAGEMENT
# =========================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def restaurant_menu_items(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id, owner=request.user)
    except Restaurant.DoesNotExist:
        return Response(
            {"error": "Restaurant not found or access denied."},
            status=status.HTTP_404_NOT_FOUND,
        )

    items = MenuItem.objects.filter(restaurant=restaurant)
    serializer = MenuItemSerializer(items, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def add_menu_item(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id, owner=request.user)
    except Restaurant.DoesNotExist:
        return Response(
            {"error": "Restaurant not found or access denied."},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = MenuItemSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(restaurant=restaurant)
        return Response(
            {"message": "Menu item added successfully"}, status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_menu_item(request, item_id):
    try:
        item = MenuItem.objects.get(id=item_id, restaurant__owner=request.user)
    except MenuItem.DoesNotExist:
        return Response(
            {"error": "Menu item not found or access denied."},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = MenuItemSerializer(item, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Menu item updated successfully"}, status=status.HTTP_200_OK
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_menu_item(request, item_id):
    try:
        item = MenuItem.objects.get(id=item_id, restaurant__owner=request.user)
    except MenuItem.DoesNotExist:
        return Response(
            {"error": "Menu item not found or access denied."},
            status=status.HTTP_404_NOT_FOUND,
        )

    item.delete()
    return Response(
        {"message": "Menu item deleted successfully"}, status=status.HTTP_200_OK
    )


# =========================
# CUSTOMER MENU
# =========================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def customer_restaurant_menu_items(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return Response(
            {"error": "Restaurant not found."}, status=status.HTTP_404_NOT_FOUND
        )

    items = MenuItem.objects.filter(restaurant=restaurant, available=True).order_by(
        "name"
    )

    serializer = MenuItemSerializer(items, many=True)
    return Response(
        {
            "restaurant_id": restaurant.id,
            "restaurant_name": restaurant.name,
            "items": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


# =========================
# CART APIs
# =========================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_cart(request):
    cart = get_or_create_cart(request.user)
    serializer = CartSerializer(cart)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    menu_item_id = request.data.get("menu_item_id")
    raw_quantity = request.data.get("quantity", 1)

    try:
        quantity = int(raw_quantity)
    except (TypeError, ValueError):
        return Response(
            {"error": "Quantity must be a valid number."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not menu_item_id:
        return Response(
            {"error": "menu_item_id is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    if quantity < 1:
        return Response(
            {"error": "Quantity must be at least 1."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        menu_item = MenuItem.objects.select_related("restaurant").get(
            id=menu_item_id, available=True
        )
    except MenuItem.DoesNotExist:
        return Response(
            {"error": "Menu item not found or unavailable."},
            status=status.HTTP_404_NOT_FOUND,
        )

    cart = get_or_create_cart(request.user)

    existing_items = cart.items.select_related("menu_item__restaurant")
    if existing_items.exists():
        existing_restaurant_id = existing_items.first().menu_item.restaurant_id
        if existing_restaurant_id != menu_item.restaurant_id:
            return Response(
                {
                    "error": "Your cart already contains items from another restaurant. Clear it before adding from a new restaurant."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        menu_item=menu_item,
        defaults={"quantity": quantity},
    )

    if not created:
        cart_item.quantity += quantity
        cart_item.save(update_fields=["quantity"])

    serializer = CartSerializer(cart)
    return Response(
        {
            "message": "Item added to cart successfully.",
            "cart": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
    except CartItem.DoesNotExist:
        return Response(
            {"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND
        )

    raw_quantity = request.data.get("quantity", 1)

    try:
        quantity = int(raw_quantity)
    except (TypeError, ValueError):
        return Response(
            {"error": "Quantity must be a valid number."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if quantity < 1:
        return Response(
            {"error": "Quantity must be at least 1."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    cart_item.quantity = quantity
    cart_item.save(update_fields=["quantity"])

    serializer = CartSerializer(cart_item.cart)
    return Response(
        {
            "message": "Cart updated successfully.",
            "cart": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_cart_item(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
    except CartItem.DoesNotExist:
        return Response(
            {"error": "Cart item not found."}, status=status.HTTP_404_NOT_FOUND
        )

    cart = cart_item.cart
    cart_item.delete()

    serializer = CartSerializer(cart)
    return Response(
        {
            "message": "Item removed from cart.",
            "cart": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    cart = get_or_create_cart(request.user)
    cart.items.all().delete()

    serializer = CartSerializer(cart)
    return Response(
        {
            "message": "Cart cleared successfully.",
            "cart": serializer.data,
        },
        status=status.HTTP_200_OK,
    )


# =========================
# ORDER APIs
# =========================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def checkout_summary(request):
    cart = get_or_create_cart(request.user)
    cart_items = list(cart.items.select_related("menu_item__restaurant"))

    if not cart_items:
        return Response(
            {"error": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST
        )

    restaurant_ids = {item.menu_item.restaurant_id for item in cart_items}
    if len(restaurant_ids) != 1:
        return Response(
            {"error": "Your cart contains items from multiple restaurants."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    restaurant = cart_items[0].menu_item.restaurant
    subtotal = cart.total_price
    delivery_charge = Decimal("60.00")

    deal = (
        Deal.objects.filter(
            restaurant=restaurant,
            active_status=True,
            minimum_order_amount__lte=subtotal,
        )
        .order_by("-discount_value")
        .first()
    )

    discount_amount = Decimal("0.00")

    if deal:
        if deal.discount_type == "percentage":
            discount_amount = (
                subtotal * deal.discount_value / Decimal("100")
            ).quantize(Decimal("0.01"))
        elif deal.discount_type == "fixed":
            discount_amount = min(deal.discount_value, subtotal)

    final_total = (subtotal - discount_amount + delivery_charge).quantize(
        Decimal("0.01")
    )

    return Response(
        {
            "restaurant_id": restaurant.id,
            "restaurant_name": restaurant.name,
            "cart": CartSerializer(cart).data,
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "delivery_charge": delivery_charge,
            "final_total": final_total,
            "applied_deal": deal.title if deal else None,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def customer_orders(request):
    orders = Order.objects.filter(customer=request.user).order_by("-created_at")
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def place_order(request):
    cart = get_or_create_cart(request.user)
    cart_items = list(cart.items.select_related("menu_item__restaurant"))

    if not cart_items:
        return Response(
            {"error": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST
        )

    restaurant_ids = {item.menu_item.restaurant_id for item in cart_items}
    if len(restaurant_ids) != 1:
        return Response(
            {"error": "You can place an order from only one restaurant at a time."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    customer_name = request.data.get("customer_name", "").strip()
    phone_number = request.data.get("phone_number", "").strip()
    delivery_address = request.data.get("delivery_address", "").strip()
    payment_method = request.data.get("payment_method", "Cash on Delivery").strip()

    if not customer_name:
        return Response(
            {"error": "Customer name is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    if not phone_number:
        return Response(
            {"error": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    if not delivery_address:
        return Response(
            {"error": "Delivery address is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    restaurant = cart_items[0].menu_item.restaurant
    subtotal = sum((item.subtotal for item in cart_items), Decimal("0.00")).quantize(
        Decimal("0.01")
    )
    delivery_charge = Decimal("60.00")

    deal = (
        Deal.objects.filter(
            restaurant=restaurant,
            active_status=True,
            minimum_order_amount__lte=subtotal,
        )
        .order_by("-discount_value")
        .first()
    )

    discount_amount = Decimal("0.00")

    if deal:
        if deal.discount_type == "percentage":
            discount_amount = (
                subtotal * deal.discount_value / Decimal("100")
            ).quantize(Decimal("0.01"))
        elif deal.discount_type == "fixed":
            discount_amount = min(deal.discount_value, subtotal)

    final_amount = (subtotal - discount_amount + delivery_charge).quantize(
        Decimal("0.01")
    )

    with transaction.atomic():
        order = Order.objects.create(
            customer=request.user,
            restaurant=restaurant,
            customer_name=customer_name,
            phone_number=phone_number,
            delivery_address=delivery_address,
            payment_method=payment_method,
            delivery_charge=delivery_charge,
            original_amount=subtotal,
            discount_amount=discount_amount,
            applied_deal_title=deal.title if deal else None,
            total_amount=final_amount,
            status="confirmed",
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                menu_item=item.menu_item,
                item_name=item.menu_item.name,
                unit_price=item.menu_item.price,
                quantity=item.quantity,
            )

        cart.items.all().delete()

    return Response(
        {
            "message": "Order placed successfully.",
            "order_id": order.id,
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "delivery_charge": delivery_charge,
            "final_amount": final_amount,
            "applied_deal": deal.title if deal else None,
            "redirect_url": f"/order-confirmation/{order.id}/",
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def order_confirmation_data(request, order_id):
    try:
        order = Order.objects.get(id=order_id, customer=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = OrderSerializer(order)
    return Response(serializer.data, status=status.HTTP_200_OK)


# =========================
# REVIEW / RATING APIs
# =========================
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def submit_review(request, order_id):
    try:
        order = Order.objects.get(id=order_id, customer=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

    if hasattr(order, "review"):
        return Response(
            {"error": "Review already submitted for this order."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    rating = request.data.get("rating")
    comment = request.data.get("comment", "").strip()

    if not rating:
        return Response(
            {"error": "Rating is required."}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return Response(
            {"error": "Rating must be a number."}, status=status.HTTP_400_BAD_REQUEST
        )

    if rating < 1 or rating > 5:
        return Response(
            {"error": "Rating must be between 1 and 5."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    review = Review.objects.create(
        user=request.user,
        restaurant=order.restaurant,
        order=order,
        rating=rating,
        comment=comment,
        is_approved=True,
    )

    update_restaurant_average_rating(order.restaurant)

    serializer = ReviewSerializer(review)
    return Response(
        {
            "message": "Review submitted successfully.",
            "review": serializer.data,
            "updated_average_rating": order.restaurant.average_rating,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def customer_restaurant_reviews(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
    except Restaurant.DoesNotExist:
        return Response(
            {"error": "Restaurant not found."}, status=status.HTTP_404_NOT_FOUND
        )

    reviews = (
        Review.objects.filter(restaurant=restaurant, is_approved=True)
        .select_related("user")
        .order_by("-created_at")
    )

    data = []
    for review in reviews:
        data.append(
            {
                "id": review.id,
                "customer_name": review.user.first_name or review.user.username,
                "rating": review.rating,
                "comment": review.comment,
                "created_at": review.created_at,
            }
        )

    return Response(
        {
            "restaurant_id": restaurant.id,
            "restaurant_name": restaurant.name,
            "reviews": data,
        }
    )


# =========================
# ADMIN PAGE
# =========================
def admin_dashboard_page(request):
    return render(request, "admin_dashboard.html")


# =========================
# ADMIN USER MANAGEMENT
# =========================
@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    if not is_admin_user(request.user):
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    if request.user.id == user_id:
        return Response(
            {"error": "You cannot delete your own admin account."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    user.delete()
    return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)


# =========================
# ADMIN REVIEW MODERATION
# =========================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_reviews(request):
    if not is_admin_user(request.user):
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    reviews = Review.objects.select_related("user", "restaurant", "order").order_by(
        "-created_at"
    )

    data = []
    for review in reviews:
        data.append(
            {
                "id": review.id,
                "restaurant_name": review.restaurant.name,
                "customer_name": review.user.first_name or review.user.username,
                "customer_email": review.user.email or review.user.username,
                "order_id": review.order.id,
                "rating": review.rating,
                "comment": review.comment,
                "is_reported": review.is_reported,
                "report_reason": review.report_reason,
                "created_at": review.created_at,
            }
        )

    return Response(data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def business_promotions(request):
    deals = Deal.objects.filter(restaurant__owner=request.user).select_related(
        "restaurant"
    )
    serializer = DealSerializer(deals, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_promotion(request, deal_id):
    try:
        deal = Deal.objects.get(id=deal_id, restaurant__owner=request.user)
    except Deal.DoesNotExist:
        return Response({"error": "Promotion not found or access denied."}, status=404)

    serializer = DealSerializer(deal, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Promotion updated successfully."}, status=200)

    return Response(serializer.errors, status=400)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_promotion(request):
    restaurant_id = request.data.get("restaurant")

    try:
        restaurant = Restaurant.objects.get(id=restaurant_id, owner=request.user)
    except Restaurant.DoesNotExist:
        return Response({"error": "Restaurant not found or access denied."}, status=404)

    serializer = DealSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(restaurant=restaurant)
        return Response({"message": "Promotion added successfully."}, status=201)

    return Response(serializer.errors, status=400)


# =========================
# ADMIN HELPERS
# =========================
def is_admin_user(user):
    try:
        return user.userprofile.role == "admin"
    except UserProfile.DoesNotExist:
        return False


# =========================
# ADMIN PAGE
# =========================
def admin_dashboard_page(request):
    return render(request, "admin_dashboard.html")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_dashboard_data(request):
    if not is_foodotg_admin(request.user):
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    user_search = request.GET.get("user_search", "").strip()
    review_search = request.GET.get("review_search", "").strip()
    report_status = request.GET.get("report_status", "all").strip()

    users = User.objects.select_related("userprofile").all().order_by("id")

    if user_search:
        users = users.filter(
            models.Q(username__icontains=user_search)
            | models.Q(email__icontains=user_search)
            | models.Q(first_name__icontains=user_search)
        )

    reviews = Review.objects.select_related("user", "restaurant", "order").order_by("-created_at")

    if review_search:
        reviews = reviews.filter(
            models.Q(comment__icontains=review_search)
            | models.Q(user__username__icontains=review_search)
            | models.Q(user__email__icontains=review_search)
            | models.Q(user__first_name__icontains=review_search)
            | models.Q(restaurant__name__icontains=review_search)
        )

    reports = ReviewReport.objects.select_related(
        "review",
        "review__restaurant",
        "reported_by",
    ).order_by("-created_at")

    if report_status == "pending":
        reports = reports.filter(resolved=False)
    elif report_status == "resolved":
        reports = reports.filter(resolved=True)

    user_data = []
    customer_data = []
    business_owner_data = []
    admin_data = []

    for user in users:
        try:
            role = user.userprofile.role
            is_banned = user.userprofile.is_banned
        except UserProfile.DoesNotExist:
            role = "customer"
            is_banned = False

        item = {
            "id": user.id,
            "name": user.first_name or user.username,
            "email": user.email or user.username,
            "username": user.username,
            "role": role,
            "is_active": user.is_active,
            "is_banned": is_banned,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "last_login": user.last_login,
            "date_joined": user.date_joined,
        }

        user_data.append(item)

        if role == "customer":
            customer_data.append(item)
        elif role == "business_owner":
            business_owner_data.append(item)
        elif role == "admin":
            admin_data.append(item)

    restaurant_data = []
    restaurants = Restaurant.objects.select_related("owner").all().order_by("id")

    for restaurant in restaurants:
        restaurant_data.append({
            "id": restaurant.id,
            "name": restaurant.name,
            "owner": restaurant.owner.first_name or restaurant.owner.username,
            "owner_email": restaurant.owner.email or restaurant.owner.username,
            "description": restaurant.description,
            "address": restaurant.address,
            "category": restaurant.category,
            "price_range": restaurant.price_range,
            "average_rating": restaurant.average_rating,
            "delivery_available": restaurant.delivery_available,
            "latitude": restaurant.latitude,
            "longitude": restaurant.longitude,
            "created_at": restaurant.created_at,
        })

    menu_item_data = []
    menu_items = MenuItem.objects.select_related("restaurant").all().order_by("id")

    for item in menu_items:
        menu_item_data.append({
            "id": item.id,
            "name": item.name,
            "restaurant": item.restaurant.name,
            "description": item.description,
            "price": str(item.price),
            "available": item.available,
            "created_at": item.created_at,
        })

    deal_data = []
    deals = Deal.objects.select_related("restaurant").all().order_by("id")

    for deal in deals:
        deal_data.append({
            "id": deal.id,
            "title": deal.title,
            "restaurant": deal.restaurant.name,
            "description": deal.description,
            "active_status": deal.active_status,
            "discount_type": deal.discount_type,
            "discount_value": str(deal.discount_value),
            "minimum_order_amount": str(deal.minimum_order_amount),
        })

    order_data = []
    orders = Order.objects.select_related(
        "customer",
        "restaurant",
        "rider",
        "rider__user",
    ).all().order_by("-created_at")

    for order in orders:
        order_data.append({
            "id": order.id,
            "customer": order.customer.first_name or order.customer.username,
            "customer_email": order.customer.email or order.customer.username,
            "restaurant": order.restaurant.name,
            "rider": order.rider.user.username if order.rider else "Not Assigned",
            "customer_name": order.customer_name,
            "phone_number": order.phone_number,
            "delivery_address": order.delivery_address,
            "payment_method": order.payment_method,
            "status": order.status,
            "original_amount": str(order.original_amount),
            "discount_amount": str(order.discount_amount),
            "delivery_charge": str(order.delivery_charge),
            "total_amount": str(order.total_amount),
            "applied_deal_title": order.applied_deal_title,
            "created_at": order.created_at,
        })

    rider_data = []
    riders = Rider.objects.select_related("user").all().order_by("id")

    for rider in riders:
        rider_data.append({
            "id": rider.id,
            "name": rider.user.first_name or rider.user.username,
            "email": rider.user.email or rider.user.username,
            "phone": rider.phone,
            "vehicle_type": rider.vehicle_type,
            "is_available": rider.is_available,
        })

    cart_data = []
    carts = Cart.objects.select_related("user").prefetch_related("items").all().order_by("id")

    for cart in carts:
        cart_data.append({
            "id": cart.id,
            "user": cart.user.first_name or cart.user.username,
            "email": cart.user.email or cart.user.username,
            "total_items": cart.total_items,
            "total_price": str(cart.total_price),
            "created_at": cart.created_at,
            "updated_at": cart.updated_at,
        })

    review_data = []
    for review in reviews:
        review_data.append({
            "id": review.id,
            "restaurant_name": review.restaurant.name,
            "customer_name": review.user.first_name or review.user.username,
            "customer_email": review.user.email or review.user.username,
            "order_id": review.order.id,
            "rating": review.rating,
            "comment": review.comment,
            "is_approved": review.is_approved,
            "is_reported": review.is_reported,
            "report_count": review.reports.count(),
            "created_at": review.created_at,
        })

    report_data = []
    for report in reports:
        report_data.append({
            "id": report.id,
            "review_id": report.review.id,
            "restaurant_name": report.review.restaurant.name,
            "review_comment": report.review.comment,
            "reported_by": report.reported_by.first_name or report.reported_by.username,
            "reason": report.reason,
            "resolved": report.resolved,
            "created_at": report.created_at,
        })

    return Response({
        "summary": {
            "total_users": len(user_data),
            "total_customers": len(customer_data),
            "total_business_owners": len(business_owner_data),
            "total_admins": len(admin_data),
            "total_riders": len(rider_data),
            "total_restaurants": len(restaurant_data),
            "total_menu_items": len(menu_item_data),
            "total_deals": len(deal_data),
            "total_orders": len(order_data),
            "total_carts": len(cart_data),
            "total_reviews": len(review_data),
            "total_reports": len(report_data),
        },
        "users": user_data,
        "customers": customer_data,
        "business_owners": business_owner_data,
        "admins": admin_data,
        "restaurants": restaurant_data,
        "menu_items": menu_item_data,
        "deals": deal_data,
        "orders": order_data,
        "riders": rider_data,
        "carts": cart_data,
        "reviews": review_data,
        "reports": report_data,
        "pagination": {
            "user_page": 1,
            "user_total": len(user_data),
            "report_page": 1,
            "report_total": len(report_data),
            "page_size": 6,
        },
    }, status=status.HTTP_200_OK)
# =========================
# ADMIN USER MANAGEMENT
# =========================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_users(request):
    if not is_admin_user(request.user):
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    users = User.objects.all().select_related("userprofile").order_by("id")

    data = []
    for user in users:
        try:
            role = user.userprofile.role
        except UserProfile.DoesNotExist:
            role = "customer"

        data.append(
            {
                "id": user.id,
                "name": user.first_name or user.username,
                "email": user.email or user.username,
                "username": user.username,
                "role": role,
                "is_staff": user.is_staff,
                "is_active": user.is_active,
            }
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def report_review(request, review_id):
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return Response({"error": "Review not found"}, status=404)

    reason = request.data.get("reason", "").strip()

    if not reason:
        return Response({"error": "Reason required"}, status=400)

    report, created = ReviewReport.objects.get_or_create(
        review=review, reported_by=request.user, defaults={"reason": reason}
    )

    if not created:
        return Response({"error": "Already reported"}, status=400)

    return Response({"message": "Reported successfully"}, status=201)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_promotion(request, deal_id):
    try:
        deal = Deal.objects.get(id=deal_id, restaurant__owner=request.user)
    except Deal.DoesNotExist:
        return Response({"error": "Promotion not found or access denied."}, status=404)

    deal.delete()
    return Response({"message": "Promotion deleted successfully."}, status=200)


def delete_user(request, user_id):
    if not is_admin_user(request.user):
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    if request.user.id == user_id:
        return Response(
            {"error": "You cannot delete your own admin account."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    user.delete()
    return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def admin_ban_user(request, user_id):
    if not is_foodotg_admin(request.user):
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    try:
        user = User.objects.select_related("userprofile").get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    if user == request.user:
        return Response({"error": "You cannot ban your own admin account."}, status=status.HTTP_400_BAD_REQUEST)

    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={"role": "customer"})
    profile.is_banned = True
    profile.save(update_fields=["is_banned"])

    user.is_active = False
    user.save(update_fields=["is_active"])

    Review.objects.filter(user=user).update(is_approved=False)

    affected_restaurants = Restaurant.objects.filter(reviews__user=user).distinct()
    for restaurant in affected_restaurants:
        update_restaurant_average_rating(restaurant)

    return Response({"message": "User banned and their reviews were hidden."})


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def admin_unban_user(request, user_id):
    if not is_foodotg_admin(request.user):
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={"role": "customer"}
    )

    profile.is_banned = False
    profile.save(update_fields=["is_banned"])

    user.is_active = True
    user.save(update_fields=["is_active"])

    return Response({"message": "User unbanned successfully."})


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def admin_update_user_status(request, user_id):
    if not is_foodotg_admin(request.user):
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    if user == request.user:
        return Response({"error": "You cannot disable your own admin account."}, status=status.HTTP_400_BAD_REQUEST)

    is_active = request.data.get("is_active")

    if is_active is None:
        return Response({"error": "is_active is required"}, status=status.HTTP_400_BAD_REQUEST)

    if isinstance(is_active, str):
        is_active = is_active.lower() == "true"

    if is_active and hasattr(user, "userprofile") and user.userprofile.is_banned:
        return Response(
            {"error": "This user is banned. Unban the user first."},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.is_active = bool(is_active)
    user.save(update_fields=["is_active"])

    return Response({
        "message": "User status updated successfully.",
        "is_active": user.is_active,
    })


# =========================
# ADMIN REVIEW MODERATION
# =========================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_reviews(request):
    if not is_admin_user(request.user):
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    reviews = Review.objects.select_related("user", "restaurant", "order").order_by(
        "-created_at"
    )

    data = []
    for review in reviews:
        data.append(
            {
                "id": review.id,
                "restaurant_name": review.restaurant.name,
                "customer_name": review.user.first_name or review.user.username,
                "customer_email": review.user.email or review.user.username,
                "order_id": review.order.id,
                "rating": review.rating,
                "comment": review.comment,
                "is_reported": review.is_reported,
                "report_reason": review.report_reason,
                "created_at": review.created_at,
            }
        )

    return Response(data, status=status.HTTP_200_OK)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def admin_resolve_review_report(request, report_id):
    if not is_foodotg_admin(request.user):
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    try:
        report = ReviewReport.objects.get(id=report_id)
    except ReviewReport.DoesNotExist:
        return Response({"error": "Report not found"}, status=status.HTTP_404_NOT_FOUND)

    report.resolved = True
    report.save(update_fields=["resolved"])

    return Response(
        {"message": "Report resolved successfully"}, status=status.HTTP_200_OK
    )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def admin_update_review_status(request, review_id):
    if not is_foodotg_admin(request.user):
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)

    is_approved = request.data.get("is_approved")

    if is_approved is None:
        return Response(
            {"error": "is_approved is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    if isinstance(is_approved, str):
        is_approved = is_approved.lower() == "true"

    review.is_approved = is_approved
    review.save(update_fields=["is_approved"])

    update_restaurant_average_rating(review.restaurant)

    return Response(
        {
            "message": "Review status updated successfully.",
            "is_approved": review.is_approved,
        },
        status=status.HTTP_200_OK,
    )


def rider_dashboard_page(request):
    return render(request, "rider_dashboard.html")


def is_rider_user(user):
    try:
        return user.userprofile.role == "rider"
    except UserProfile.DoesNotExist:
        return False


def rider_login_page(request):
    return render(request, "rider_login.html")


def rider_register_page(request):
    return render(request, "rider_register.html")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_riders(request):
    if not is_admin_user(request.user):
        return Response({"error": "Unauthorized"}, status=403)

    riders = Rider.objects.select_related("user").all()

    data = []
    for rider in riders:
        data.append(
            {
                "id": rider.id,
                "name": rider.user.first_name or rider.user.username,
                "email": rider.user.email or rider.user.username,
                "phone": rider.phone,
                "vehicle_type": rider.vehicle_type,
                "is_available": rider.is_available,
            }
        )

    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_orders(request):
    if not is_admin_user(request.user):
        return Response({"error": "Unauthorized"}, status=403)

    orders = Order.objects.select_related(
        "customer", "restaurant", "rider", "rider__user"
    ).order_by("-created_at")

    data = []
    for order in orders:
        data.append(
            {
                "id": order.id,
                "customer": order.customer.email or order.customer.username,
                "restaurant_name": order.restaurant.name,
                "status": order.status,
                "total_amount": order.total_amount,
                "rider_id": order.rider.id if order.rider else None,
                "rider_name": (
                    order.rider.user.username if order.rider else "Not Assigned"
                ),
                "created_at": order.created_at,
            }
        )

    return Response(data)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def approve_review(request, review_id):
    if not is_admin_user(request.user):
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)

    review.is_approved = True
    review.save(update_fields=["is_approved"])

    update_restaurant_average_rating(review.restaurant)

    return Response(
        {"message": "Review approved successfully"}, status=status.HTTP_200_OK
    )


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def delete_review(request, review_id):
    if not is_foodotg_admin(request.user):
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return Response({"error": "Review not found"}, status=status.HTTP_404_NOT_FOUND)

    restaurant = review.restaurant
    review.delete()

    update_restaurant_average_rating(restaurant)

    return Response(
        {"message": "Review deleted successfully"}, status=status.HTTP_200_OK
    )


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def assign_rider_to_order(request, order_id):
    if not is_admin_user(request.user):
        return Response({"error": "Unauthorized"}, status=403)

    rider_id = request.data.get("rider_id")

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({"error": "Order not found"}, status=404)

    try:
        rider = Rider.objects.get(id=rider_id, is_available=True)
    except Rider.DoesNotExist:
        return Response({"error": "Rider not found or unavailable"}, status=404)

    order.rider = rider
    order.save(update_fields=["rider"])

    rider.is_available = False
    rider.save(update_fields=["is_available"])

    return Response({"message": "Rider assigned successfully"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def rider_orders(request):
    if not is_rider_user(request.user):
        return Response({"error": "Unauthorized"}, status=403)

    try:
        rider = request.user.rider_profile
    except Rider.DoesNotExist:
        return Response({"error": "Rider profile not found"}, status=404)

    orders = (
        Order.objects.filter(rider=rider)
        .select_related("restaurant", "customer")
        .order_by("-created_at")
    )

    data = []
    for order in orders:
        data.append(
            {
                "id": order.id,
                "customer": order.customer.email or order.customer.username,
                "restaurant_name": order.restaurant.name,
                "restaurant_address": order.restaurant.address,
                "status": order.status,
                "total_amount": order.total_amount,
                "created_at": order.created_at,
            }
        )

    return Response(data)


# TEMP store (for demo; later use DB model)
reset_tokens = {}


@api_view(["POST"])
def forgot_password(request):
    email = request.data.get("email")

    user = User.objects.filter(email=email).first()

    if not user:
        return Response({"error": "Email not found"}, status=404)

    token = str(uuid.uuid4())
    reset_tokens[token] = user.id

    reset_link = f"http://127.0.0.1:8000/reset-password/{token}/"

    # For now print instead of email
    print("RESET LINK:", reset_link)

    return Response({"message": "Password reset link sent (check console)"})


reset_tokens = {}


@api_view(["POST"])
def forgot_password(request):
    email = request.data.get("email", "").strip()

    if not email:
        return Response({"error": "Email is required"}, status=400)

    user = User.objects.filter(email=email).first()

    if not user:
        return Response({"error": "Email not found"}, status=404)

    token = str(uuid.uuid4())
    reset_tokens[token] = user.id

    reset_link = f"http://127.0.0.1:8000/reset-password/{token}/"

    send_mail(
        subject="FoodOTG Password Reset",
        message=f"Click this link to reset your password:\n\n{reset_link}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )

    return Response({"message": "Password reset link sent to your email."})


@api_view(["POST"])
def reset_password(request, token):
    new_password = request.data.get("password", "").strip()

    if not new_password:
        return Response({"error": "Password is required"}, status=400)

    if token not in reset_tokens:
        return Response({"error": "Invalid token"}, status=400)

    user_id = reset_tokens[token]
    user = User.objects.get(id=user_id)

    user.set_password(new_password)
    user.save()

    del reset_tokens[token]

    return Response({"message": "Password reset successful"})


def forgot_password_page(request):
    return render(request, "forgot_password.html")


def reset_password_page(request, token):
    return render(request, "reset_password.html", {"token": token})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_invoice(request, order_id):
    try:
        order = Order.objects.get(id=order_id, customer=request.user)
    except Order.DoesNotExist:
        return Response({"error": "Order not found."}, status=status.HTTP_404_NOT_FOUND)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="invoice_order_{order.id}.pdf"'
    )

    p = canvas.Canvas(response)

    p.setFont("Helvetica-Bold", 18)
    p.drawString(200, 800, "FoodOTG Invoice")

    p.setFont("Helvetica", 12)
    p.drawString(50, 760, f"Order ID: #{order.id}")
    p.drawString(50, 740, f"Restaurant: {order.restaurant.name}")
    p.drawString(50, 720, f"Customer: {order.customer_name}")
    p.drawString(50, 700, f"Phone: {order.phone_number}")
    p.drawString(50, 680, f"Address: {order.delivery_address}")
    p.drawString(50, 660, f"Payment: {order.payment_method}")
    p.drawString(50, 640, f"Status: {order.status}")

    y = 600
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Items")
    y -= 25

    p.setFont("Helvetica", 11)

    for item in order.items.all():
        p.drawString(50, y, f"{item.item_name} x {item.quantity}")
        p.drawString(400, y, f"Tk {item.subtotal}")
        y -= 22

    y -= 20
    p.drawString(50, y, f"Subtotal: Tk {order.original_amount}")
    y -= 20
    p.drawString(50, y, f"Discount: Tk {order.discount_amount}")
    y -= 20
    p.drawString(50, y, f"Delivery Charge: Tk {order.delivery_charge}")
    y -= 30

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, f"Final Total: Tk {order.total_amount}")

    p.showPage()
    p.save()

    return response
