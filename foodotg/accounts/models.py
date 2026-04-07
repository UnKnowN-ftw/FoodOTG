from django.db import models
from django.contrib.auth.models import User

# =========================
# 🍽 Restaurant Model
# =========================
class Restaurant(models.Model):
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    price_range = models.CharField(max_length=50)

    def __str__(self):
        return self.name


# =========================
# 🎁 Deal Model
# =========================
class Deal(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    active_status = models.BooleanField(default=True)

    def __str__(self):
        return self.title


# =========================
# 🎯 User Preferences
# =========================
class Preference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    budget_range = models.CharField(max_length=50)

    def __str__(self):
        return self.user.username