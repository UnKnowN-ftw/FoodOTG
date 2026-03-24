from django.contrib.auth.models import User
from rest_framework import serializers
import re

class RegisterSerializer(serializers.ModelSerializer):
    # Mapping 'name' from UI to Django internal field
    name = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate_email(self, value):
        # NFR-10: Privacy and validation check [cite: 100]
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_password(self, value):
        # NFR-03: Security/Complexity requirements [cite: 97]
        if len(value) < 6:
            raise serializers.ValidationError("Security requires 6+ characters.")
        if not re.search(r'[A-Za-z]', value) or not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password must contain both letters and numbers.")
        return value

    def create(self, validated_data):
        # Creating user with Email as Username as per SDS [cite: 779, 941]
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['name']
        )
        return user