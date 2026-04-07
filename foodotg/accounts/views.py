from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render

from .serializers import RegisterSerializer, RestaurantSerializer, DealSerializer
from .models import Restaurant, Deal, Preference


# =========================
# 🔐 REGISTER API (FR-01)
# =========================
@api_view(['POST'])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Registration is Complete"}, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# =========================
# 🔐 LOGIN API (FR-02)
# =========================
@api_view(['POST'])
def user_login(request):
    email = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=email, password=password)

    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": "End User",
            "message": "Login successful"
        }, status=status.HTTP_200_OK)

    return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)


# =========================
# 🔓 LOGOUT API
# =========================
@api_view(['POST'])
def user_logout(request):
    return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)


# =========================
# 🎯 SAVE PREFERENCES API
# =========================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_preferences(request):
    preferences = request.data.get('preferences', [])

    pref_obj, created = Preference.objects.get_or_create(user=request.user)
    pref_obj.taste_preferences = preferences
    pref_obj.save()

    return Response({
        "message": "Preferences saved successfully",
        "preferences": pref_obj.taste_preferences
    })


# =========================
# 🌐 PAGES (UI)
# =========================
def login_page(request):
    return render(request, 'login.html')


def register_page(request):
    return render(request, 'register.html')


def dashboard(request):
    return render(request, 'dashboard.html')


# =========================
# 📊 DASHBOARD DATA API
# =========================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_data(request):
    restaurants = Restaurant.objects.all()
    deals = Deal.objects.filter(active_status=True)

    restaurant_data = RestaurantSerializer(restaurants, many=True).data
    deal_data = DealSerializer(deals, many=True).data

    # Get user preferences
    user_preferences = []
    try:
        pref = Preference.objects.get(user=request.user)
        user_preferences = pref.taste_preferences
    except Preference.DoesNotExist:
        pass

    return Response({
        "businesses": restaurant_data,
        "deals": deal_data,
        "preferences": user_preferences
    })