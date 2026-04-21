from django.urls import path
from . import views

urlpatterns = [
    path("api/register/", views.register),
    path("api/login/", views.user_login),
    path("api/logout/", views.user_logout),

    path("api/dashboard/", views.dashboard_data),
    path("api/save-preferences/", views.save_preferences),

    path("api/business-dashboard/", views.business_dashboard_data),
    path("api/business-reviews/", views.business_reviews),
    path("api/add-restaurant/", views.add_restaurant),

    path("api/restaurants/<int:restaurant_id>/menu/", views.restaurant_menu_items),
    path("api/restaurants/<int:restaurant_id>/menu/add/", views.add_menu_item),
    path("api/menu-items/<int:item_id>/update/", views.update_menu_item),
    path("api/menu-items/<int:item_id>/delete/", views.delete_menu_item),

    path("api/customer/restaurants/<int:restaurant_id>/menu/", views.customer_restaurant_menu_items),

    path("api/cart/", views.get_cart),
    path("api/cart/add/", views.add_to_cart),
    path("api/cart/clear/", views.clear_cart),
    path("api/cart/items/<int:item_id>/update/", views.update_cart_item),
    path("api/cart/items/<int:item_id>/delete/", views.remove_cart_item),

    path("api/checkout/summary/", views.checkout_summary),

    path("api/orders/", views.customer_orders),
    path("api/orders/place/", views.place_order),
    path("api/orders/<int:order_id>/confirmation/", views.order_confirmation_data),
    path("api/orders/<int:order_id>/review/", views.submit_review),

    path("login/", views.login_page),
    path("register/", views.register_page),

    path("customer-login/", views.customer_login_page),
    path("customer-register/", views.customer_register_page),
    path("customer-dashboard/", views.customer_dashboard_page),
    path("checkout/", views.checkout_page),

    path("business-login/", views.business_login_page),
    path("business-register/", views.business_register_page),
    path("business-dashboard/", views.business_dashboard_page),

    path("order-confirmation/<int:order_id>/", views.order_confirmation_page),
]