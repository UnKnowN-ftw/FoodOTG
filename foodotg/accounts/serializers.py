from django.contrib.auth.models import User
from rest_framework import serializers
import re
from .models import Restaurant, Deal, Preference, UserProfile, MenuItem


class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(
        choices=[('customer', 'Customer'), ('business_owner', 'Business Owner')]
    )

    class Meta:
        model = User
        fields = ['name', 'email', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate_email(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Security requires 6+ characters.")
        if not re.search(r'[A-Za-z]', value) or not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password must contain both letters and numbers.")
        return value

    def create(self, validated_data):
        role = validated_data.pop('role')

        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['name']
        )

        UserProfile.objects.create(user=user, role=role)
        return user


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = '__all__'
        read_only_fields = ['owner', 'average_rating', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        return Restaurant.objects.create(owner=request.user, **validated_data)


class DealSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)

    class Meta:
        model = Deal
        fields = ['id', 'title', 'description', 'active_status', 'restaurant_name']


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = ['id', 'user', 'budget_range', 'taste_preferences']
        
        
class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = '__all__'
        read_only_fields = ['restaurant', 'created_at']