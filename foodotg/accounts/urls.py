from django.urls import path
from . import views
urlpatterns = [
    path('api/register/', views.register, name='register'),
    path('api/login/', views.user_login, name='login'),
    path('api/logout/', views.user_logout, name='logout'),

    path('login/', views.login_page, name='login_page'),
    path('dashboard/', views.dashboard, name='dashboard'),
]