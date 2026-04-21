from decimal import Decimal

from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Avg
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

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
from .serializers import (
    CartSerializer,
    DealSerializer,
    MenuItemSerializer,
    OrderSerializer,
    RegisterSerializer,
    RestaurantSerializer,
    ReviewSerializer,
)


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def update_restaurant_average_rating(restaurant):
    avg_rating = Review.objects.filter(
        restaurant=restaurant,
        is_approved=True
    ).aggregate(avg=Avg("rating"))["avg"] or 0.0

    restaurant.average_rating = round(float(avg_rating), 1)
    restaurant.save(update_fields=["average_rating"])


@api_view(["POST"])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Registration is Complete"},
            status=status.HTTP_201_CREATED
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
        {"error": "Invalid email or password"},
        status=status.HTTP_401_UNAUTHORIZED
    )


@api_view(["POST"])
def user_logout(request):
    return Response(
        {"message": "Logout successful"},
        status=status.HTTP_200_OK
    )


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
    reviews = Review.objects.filter(
        restaurant__owner=request.user,
        is_approved=True
    ).select_related("restaurant", "user", "order").order_by("-created_at")

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
def add_restaurant(request):
    serializer = RestaurantSerializer(
        data=request.data,
        context={"request": request}
    )

    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Restaurant added successfully"},
            status=status.HTTP_201_CREATED
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
            {"message": "Menu item added successfully"},
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
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
            {"message": "Menu item updated successfully"},
            status=status.HTTP_200_OK
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
        {"message": "Menu item deleted successfully"},
        status=status.HTTP_200_OK
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
            {"error": "Restaurant not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    items = MenuItem.objects.filter(
        restaurant=restaurant,
        available=True
    ).order_by("name")

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
            status=status.HTTP_400_BAD_REQUEST
        )

    if not menu_item_id:
        return Response(
            {"error": "menu_item_id is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if quantity < 1:
        return Response(
            {"error": "Quantity must be at least 1."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        menu_item = MenuItem.objects.select_related("restaurant").get(
            id=menu_item_id,
            available=True
        )
    except MenuItem.DoesNotExist:
        return Response(
            {"error": "Menu item not found or unavailable."},
            status=status.HTTP_404_NOT_FOUND
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
            {"error": "Cart item not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    raw_quantity = request.data.get("quantity", 1)

    try:
        quantity = int(raw_quantity)
    except (TypeError, ValueError):
        return Response(
            {"error": "Quantity must be a valid number."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if quantity < 1:
        return Response(
            {"error": "Quantity must be at least 1."},
            status=status.HTTP_400_BAD_REQUEST
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
            {"error": "Cart item not found."},
            status=status.HTTP_404_NOT_FOUND
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
            {"error": "Your cart is empty."},
            status=status.HTTP_400_BAD_REQUEST
        )

    restaurant_ids = {item.menu_item.restaurant_id for item in cart_items}
    if len(restaurant_ids) != 1:
        return Response(
            {"error": "Your cart contains items from multiple restaurants."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    restaurant = cart_items[0].menu_item.restaurant
    serializer = CartSerializer(cart)

    return Response(
        {
            "restaurant_id": restaurant.id,
            "restaurant_name": restaurant.name,
            "cart": serializer.data,
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
            {"error": "Your cart is empty."},
            status=status.HTTP_400_BAD_REQUEST
        )

    restaurant_ids = {item.menu_item.restaurant_id for item in cart_items}
    if len(restaurant_ids) != 1:
        return Response(
            {"error": "You can place an order from only one restaurant at a time."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    restaurant = cart_items[0].menu_item.restaurant
    total_amount = sum(
        (item.subtotal for item in cart_items),
        Decimal("0.00")
    ).quantize(Decimal("0.01"))

    with transaction.atomic():
        order = Order.objects.create(
            customer=request.user,
            restaurant=restaurant,
            total_amount=total_amount,
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

    notification_sent = False
    if request.user.email:
        try:
            send_mail(
                subject=f"FoodOTG Order Confirmation #{order.id}",
                message=(
                    f"Hello {request.user.first_name or request.user.username},\n\n"
                    f"Your order #{order.id} has been confirmed.\n"
                    f"Restaurant: {restaurant.name}\n"
                    f"Total: ৳{order.total_amount}\n\n"
                    f"Thank you for ordering with FoodOTG."
                ),
                from_email=None,
                recipient_list=[request.user.email],
                fail_silently=True,
            )
            notification_sent = True
        except Exception:
            notification_sent = False

    return Response(
        {
            "message": "Order placed successfully.",
            "order_id": order.id,
            "notification_sent": notification_sent,
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
        return Response(
            {"error": "Order not found."},
            status=status.HTTP_404_NOT_FOUND
        )

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
        return Response(
            {"error": "Order not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    if hasattr(order, "review"):
        return Response(
            {"error": "Review already submitted for this order."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    rating = request.data.get("rating")
    comment = request.data.get("comment", "").strip()

    if not rating:
        return Response(
            {"error": "Rating is required."},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        rating = int(rating)
    except (TypeError, ValueError):
        return Response(
            {"error": "Rating must be a number."},
            status=status.HTTP_400_BAD_REQUEST
        )

    if rating < 1 or rating > 5:
        return Response(
            {"error": "Rating must be between 1 and 5."},
            status=status.HTTP_400_BAD_REQUEST
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