from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render

from .serializers import RegisterSerializer, RestaurantSerializer, DealSerializer, MenuItemSerializer
from .models import Restaurant, Deal, Preference, UserProfile, MenuItem


@api_view(['POST'])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Registration is Complete"}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
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

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": role,
            "message": "Login successful"
        }, status=status.HTTP_200_OK)

    return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def user_logout(request):
    return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_preferences(request):
    preferences = request.data.get('preferences', [])
    budget_range = request.data.get('budget_range', '')

    pref_obj, created = Preference.objects.get_or_create(user=request.user)
    pref_obj.taste_preferences = preferences
    pref_obj.budget_range = budget_range
    pref_obj.save()

    return Response({
        "message": "Preferences saved successfully",
        "preferences": pref_obj.taste_preferences,
        "budget_range": pref_obj.budget_range
    })
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_restaurants(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    location = request.GET.get('location', '')

    restaurants = Restaurant.objects.all()

    if query:
        restaurants = restaurants.filter(name__icontains=query) | Restaurant.objects.filter(category__icontains=query)

    if category and category != "All":
        restaurants = restaurants.filter(category=category)

    if location and location != "All":
        restaurants = restaurants.filter(address__icontains=location)

    serializer = RestaurantSerializer(restaurants.distinct(), many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

# =========================
# PAGE VIEWS
# =========================
def login_page(request):
    return render(request, 'login.html')


def customer_login_page(request):
    return render(request, 'customer_login.html')


def business_login_page(request):
    return render(request, 'business_login.html')


def register_page(request):
    return render(request, 'register.html')


def customer_register_page(request):
    return render(request, 'customer_register.html')


def business_register_page(request):
    return render(request, 'business_register.html')


def customer_dashboard_page(request):
    return render(request, 'customer_dashboard.html')


def business_dashboard_page(request):
    return render(request, 'business_dashboard.html')


# =========================
# CUSTOMER DASHBOARD DATA
# =========================
@api_view(['GET'])
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

    return Response({
        "businesses": restaurant_data,
        "deals": deal_data,
        "preferences": user_preferences,
        "budget_range": budget_range
    })


# =========================
# BUSINESS DASHBOARD DATA
# =========================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def business_dashboard_data(request):
    restaurants = Restaurant.objects.filter(owner=request.user)
    serializer = RestaurantSerializer(restaurants, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_restaurant(request):
    serializer = RestaurantSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Restaurant added successfully"}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def restaurant_menu_items(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id, owner=request.user)
    except Restaurant.DoesNotExist:
        return Response({"error": "Restaurant not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

    items = MenuItem.objects.filter(restaurant=restaurant)
    serializer = MenuItemSerializer(items, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_menu_item(request, restaurant_id):
    try:
        restaurant = Restaurant.objects.get(id=restaurant_id, owner=request.user)
    except Restaurant.DoesNotExist:
        return Response({"error": "Restaurant not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

    serializer = MenuItemSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(restaurant=restaurant)
        return Response({"message": "Menu item added successfully"}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_menu_item(request, item_id):
    try:
        item = MenuItem.objects.get(id=item_id, restaurant__owner=request.user)
    except MenuItem.DoesNotExist:
        return Response({"error": "Menu item not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

    serializer = MenuItemSerializer(item, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Menu item updated successfully"}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_menu_item(request, item_id):
    try:
        item = MenuItem.objects.get(id=item_id, restaurant__owner=request.user)
    except MenuItem.DoesNotExist:
        return Response({"error": "Menu item not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

    item.delete()
    return Response({"message": "Menu item deleted successfully"}, status=status.HTTP_200_OK)