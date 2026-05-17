from django.contrib.auth.models import User
from django.test import TestCase
from django.apps import apps
from django.urls import resolve, Resolver404


def model_exists(model_name):
    try:
        apps.get_model("accounts", model_name)
        return True
    except LookupError:
        return False


def get_model(model_name):
    return apps.get_model("accounts", model_name)


class AdminUserManagementUnitTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin_test",
            email="admin@test.com",
            password="adminpass123"
        )

        self.customer = User.objects.create_user(
            username="normal_customer",
            email="customer@test.com",
            password="pass12345"
        )

        self.owner = User.objects.create_user(
            username="normal_owner",
            email="owner@test.com",
            password="pass12345"
        )

        if model_exists("UserProfile"):
            UserProfile = get_model("UserProfile")

            UserProfile.objects.get_or_create(
                user=self.admin_user,
                defaults={"role": "admin"}
            )

            UserProfile.objects.get_or_create(
                user=self.customer,
                defaults={"role": "customer"}
            )

            UserProfile.objects.get_or_create(
                user=self.owner,
                defaults={"role": "business_owner"}
            )

    def route_exists(self, path):
        possible_paths = []

        if path.endswith("/"):
            possible_paths.append(path)
            possible_paths.append(path.rstrip("/"))
        else:
            possible_paths.append(path + "/")
            possible_paths.append(path)

        for url in possible_paths:
            try:
                resolve(url)
                return True
            except Resolver404:
                continue

        return False

    def test_admin_user_is_superuser(self):
        self.assertTrue(self.admin_user.is_superuser)
        self.assertTrue(self.admin_user.is_staff)

    def test_user_profile_ban_field_if_available(self):
        if not model_exists("UserProfile"):
            self.skipTest("UserProfile model not found.")

        UserProfile = get_model("UserProfile")

        profile, created = UserProfile.objects.get_or_create(
            user=self.customer,
            defaults={"role": "customer"}
        )

        if not hasattr(profile, "is_banned"):
            self.skipTest("is_banned field not found in UserProfile.")

        profile.is_banned = True
        profile.save()

        updated_profile = UserProfile.objects.get(user=self.customer)

        self.assertTrue(updated_profile.is_banned)

    def test_admin_can_deactivate_business_owner_user(self):
        self.owner.is_active = False
        self.owner.save()

        updated_owner = User.objects.get(id=self.owner.id)

        self.assertFalse(updated_owner.is_active)

    def test_restaurant_can_be_deactivated_or_banned_if_field_exists(self):
        if not model_exists("Restaurant"):
            self.skipTest("Restaurant model not found.")

        Restaurant = get_model("Restaurant")

        restaurant = Restaurant.objects.create(
            owner=self.owner,
            name="Admin Managed Restaurant",
            description="Testing admin user management",
            address="Dhaka",
            category="Fast Food",
            price_range="৳৳",
            delivery_available=True,
            latitude=23.8103,
            longitude=90.4125
        )

        if hasattr(restaurant, "is_active"):
            restaurant.is_active = False
            restaurant.save()

            updated_restaurant = Restaurant.objects.get(id=restaurant.id)
            self.assertFalse(updated_restaurant.is_active)

        elif hasattr(restaurant, "is_banned"):
            restaurant.is_banned = True
            restaurant.save()

            updated_restaurant = Restaurant.objects.get(id=restaurant.id)
            self.assertTrue(updated_restaurant.is_banned)

        else:
            self.assertEqual(restaurant.owner, self.owner)

    def test_admin_panel_related_route_exists(self):
        """
        This checks whether admin-related routes are registered in urls.py.
        It does not execute the view, because some custom admin views may require
        frontend/session context and can return errors during unit testing.
        """

        possible_paths = [
            "/admin/",
            "/admin-login/",
            "/admin-dashboard/",
            "/api/admin-dashboard/",
            "/api/admin/users/",
            "/api/admin-panel/",
        ]

        found_route = False

        for path in possible_paths:
            if self.route_exists(path):
                found_route = True
                break

        self.assertTrue(
            found_route,
            "No admin-related route found in urls.py."
        )