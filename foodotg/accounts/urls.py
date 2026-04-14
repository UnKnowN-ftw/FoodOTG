from django.urls import path
from . import views

urlpatterns = [


    path('api/register/', views.register),
    path('api/login/', views.user_login),
    path('api/logout/', views.user_logout),


    path('api/dashboard/', views.dashboard_data),
    path('api/save-preferences/', views.save_preferences),


    path('api/business-dashboard/', views.business_dashboard_data),
    path('api/add-restaurant/', views.add_restaurant),
	path('api/search-restaurants/', views.search_restaurants),


    path('api/restaurants/<int:restaurant_id>/menu/', views.restaurant_menu_items),
    path('api/restaurants/<int:restaurant_id>/menu/add/', views.add_menu_item),
    path('api/menu-items/<int:item_id>/update/', views.update_menu_item),
    path('api/menu-items/<int:item_id>/delete/', views.delete_menu_item),


    path('login/', views.login_page),
    path('register/', views.register_page),


    path('customer-login/', views.customer_login_page),
    path('customer-register/', views.customer_register_page),
    path('customer-dashboard/', views.customer_dashboard_page),


    path('business-login/', views.business_login_page),
    path('business-register/', views.business_register_page),
    path('business-dashboard/', views.business_dashboard_page),
	

    path('api/restaurants/<int:restaurant_id>/promotions/', views.restaurant_promotions),
    path('api/restaurants/<int:restaurant_id>/promotions/add/', views.add_promotion),
    path('api/promotions/<int:deal_id>/update/', views.update_promotion),
    path('api/promotions/<int:deal_id>/delete/', views.delete_promotion),
]