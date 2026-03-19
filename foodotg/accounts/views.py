from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render
from .serializers import RegisterSerializer


# =========================
# 🔐 REGISTER API
# =========================
@api_view(['POST'])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User registered successfully"}, status=201)
    return Response(serializer.errors, status=400)


# =========================
# 🔐 LOGIN API
# =========================
@api_view(['POST'])
def user_login(request):   # ✅ renamed (avoids conflict with Django login)
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)

    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "message": "Login successful"
        }, status=200)

    return Response({"error": "Invalid credentials"}, status=401)


# =========================
# 🔓 LOGOUT API
# =========================
@api_view(['POST'])
def user_logout(request):
    """
    For JWT, logout is handled on client side by deleting token.
    Optional: implement blacklist if needed.
    """
    return Response({"message": "Logout successful"}, status=200)


def login_page(request):
    return render(request, 'login.html')

def dashboard(request):
    return render(request, 'dashboard.html')