from django.urls import path
from . import views

urlpatterns = [
    path('api/register/', views.register),
    path('register/', views.register_page),

    path('api/login/', views.user_login),
    path('api/logout/', views.user_logout),

    path('login/', views.login_page),
    path('dashboard/', views.dashboard),
    path('api/dashboard/', views.dashboard_data),
]