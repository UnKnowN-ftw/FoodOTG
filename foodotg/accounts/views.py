from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import render
from .serializers import RegisterSerializer

# =========================
# 🔐 REGISTER API (FR-01)
# =========================
@api_view(['POST'])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        # Returns the specific message requested for the UI overlay
        return Response({"message": "Registration is Complete"}, status=status.HTTP_201_CREATED)
    
    # Returns specific error (e.g., "User already exists") to the UI
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# =========================
# 🔐 LOGIN API (FR-02)
# =========================
@api_view(['POST'])
def user_login(request):
    # SDS uses Email for login; we map 'username' to the email field
    email = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=email, password=password)

    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": "End User", # Role-Based Access Control per SDS 7.1
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
# 🌐 PAGES (UI)
# =========================
def login_page(request):
    return render(request, 'login.html')

def register_page(request):
    return render(request, 'register.html')

def dashboard(request):
    return render(request, 'dashboard.html')