from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.timezone import now


class UserProfile(models.Model):
    ROLE_CHOICES = (
        ("customer", "Customer"),
        ("business_owner", "Business Owner"),
        ("admin", "Admin"),
        ("rider", "Rider"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_banned = models.BooleanField(default=False)

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
    image = models.ImageField(upload_to="restaurants/", blank=True, null=True)
    created_at = models.DateTimeField(default=now, editable=False)

    def __str__(self):
        return self.name


class Deal(models.Model):
    DISCOUNT_TYPE_CHOICES = (
        ("percentage", "Percentage"),
        ("fixed", "Fixed Amount"),
    )

    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    active_status = models.BooleanField(default=True)

    discount_type = models.CharField(
        max_length=20,
        choices=DISCOUNT_TYPE_CHOICES,
        default="percentage"
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

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
    image = models.ImageField(upload_to="menu_items/", blank=True, null=True)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=now, editable=False)

    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(default=now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart - {self.user.username}"

    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        total = sum((item.subtotal for item in self.items.all()), Decimal("0.00"))
        return total.quantize(Decimal("0.01"))


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(default=now, editable=False)

    class Meta:
        unique_together = ('cart', 'menu_item')

    def __str__(self):
        return f"{self.menu_item.name} x {self.quantity}"

    @property
    def subtotal(self):
        return (self.menu_item.price * self.quantity).quantize(Decimal("0.01"))


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('on_the_way', 'On The Way'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')

    rider = models.ForeignKey(
        'Rider',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_orders"
    )

    customer_name = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    delivery_address = models.TextField(blank=True, null=True)
    payment_method = models.CharField(max_length=50, default="Cash on Delivery")
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, default=60.00)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    original_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    applied_deal_title = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=now, editable=False)

    def __str__(self):
        return f"Order #{self.id} - {self.customer.username} - {self.restaurant.name}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.item_name} x {self.quantity}"

    @property
    def subtotal(self):
        return (self.unit_price * self.quantity).quantize(Decimal("0.01"))


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='reviews')
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='review')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)
    is_approved = models.BooleanField(default=True)

    is_reported = models.BooleanField(default=False)
    report_reason = models.TextField(blank=True, null=True)
    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_reviews"
    )

    created_at = models.DateTimeField(default=now, editable=False)

    def __str__(self):
        return f"{self.restaurant.name} - {self.rating}/5 by {self.user.username}"
    

class ReviewReport(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="reports"
    )
    reported_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="review_reports"
    )
    reason = models.TextField()
    resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=now, editable=False)

    class Meta:
        unique_together = ("review", "reported_by")

    def __str__(self):
        return f"Report #{self.id} for Review #{self.review.id}"

    
class Rider(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="rider_profile")
    phone = models.CharField(max_length=20, blank=True, null=True)
    vehicle_type = models.CharField(max_length=50, blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - Rider"

