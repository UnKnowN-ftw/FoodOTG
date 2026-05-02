from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    # ================= AUTH APIs =================
    path("api/register/", views.register),
    path("api/login/", views.user_login),
    path("api/logout/", views.user_logout),

    # ================= CUSTOMER =================
    path("api/dashboard/", views.dashboard_data),
    path("api/save-preferences/", views.save_preferences),

    # ================= BUSINESS =================
    path("api/business-dashboard/", views.business_dashboard_data),
    path("api/business-reviews/", views.business_reviews),
    path("api/add-restaurant/", views.add_restaurant),

    path("api/restaurants/<int:restaurant_id>/menu/", views.restaurant_menu_items),
    path("api/restaurants/<int:restaurant_id>/menu/add/", views.add_menu_item),
    path("api/menu-items/<int:item_id>/update/", views.update_menu_item),
    path("api/menu-items/<int:item_id>/delete/", views.delete_menu_item),

    path("api/customer/restaurants/<int:restaurant_id>/menu/", views.customer_restaurant_menu_items),

    # ================= CART =================
    path("api/cart/", views.get_cart),
    path("api/cart/add/", views.add_to_cart),
    path("api/cart/clear/", views.clear_cart),
    path("api/cart/items/<int:item_id>/update/", views.update_cart_item),
    path("api/cart/items/<int:item_id>/delete/", views.remove_cart_item),

    # ================= ORDER =================
    path("api/checkout/summary/", views.checkout_summary),
    path("api/orders/", views.customer_orders),
    path("api/orders/place/", views.place_order),
    path("api/orders/<int:order_id>/confirmation/", views.order_confirmation_data),
    path("api/orders/<int:order_id>/review/", views.submit_review),

    # ================= PAGES =================
    path("login/", views.login_page, name="login"),
    path("register/", views.register_page, name="register"),

    path("customer-login/", views.customer_login_page, name="customer_login"),
    path("customer-register/", views.customer_register_page),
    path("customer-dashboard/", views.customer_dashboard_page, name="customer_dashboard"),

    path("business-login/", views.business_login_page, name="business_login"),  # 🔥 FIXED
    path("business-register/", views.business_register_page),
    path("business-dashboard/", views.business_dashboard_page, name="business_dashboard"),

    path("checkout/", views.checkout_page),
    path("order-confirmation/<int:order_id>/", views.order_confirmation_page),

    # ================= ADMIN =================
    path("admin-login/", views.admin_login_page, name="admin_login"),
    path("admin-dashboard/", views.admin_dashboard_page, name="admin_dashboard"),

    path("api/admin/users/", views.admin_users),
    path("api/admin/users/<int:user_id>/delete/", views.delete_user),

    path("api/admin/reviews/", views.admin_reviews),
    path("api/admin/reviews/<int:review_id>/approve/", views.approve_review),
    path("api/admin/reviews/<int:review_id>/delete/", views.delete_review),

    # ================= RIDER =================
    path("rider-dashboard/", views.rider_dashboard_page, name="rider_dashboard"),

    path("api/admin/riders/", views.admin_riders),
    path("api/admin/orders/", views.admin_orders),
    path("api/admin/orders/<int:order_id>/assign-rider/", views.assign_rider_to_order),

    path("api/rider/orders/", views.rider_orders),

    # ================= REPORT =================
    path("api/reviews/<int:review_id>/report/", views.report_review),

    # ================= PASSWORD RESET =================

    path("forgot-password/", views.forgot_password_page),
    path("reset-password/<str:token>/", views.reset_password_page),
	path("forgot-password/", views.forgot_password_page),
    
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)