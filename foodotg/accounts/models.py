from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('business_owner', 'Business Owner'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Restaurant(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='restaurants')
    name = models.CharField(max_length=255)
    description = models.TextField()
    address = models.CharField(max_length=255)
    latitude = models.FloatField(default=23.8103)
    longitude = models.FloatField(default=90.4125)
    category = models.CharField(max_length=100)
    price_range = models.CharField(max_length=50)
    average_rating = models.FloatField(default=0.0)
    delivery_available = models.BooleanField(default=True)
    image = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(default=now, editable=False)

    def __str__(self):
        return self.name


class Deal(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    active_status = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Preference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    budget_range = models.CharField(max_length=50, blank=True, null=True)
    taste_preferences = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.user.username
    
class MenuItem(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=now, editable=False)

    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"