from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from users.models import User


class AccountSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']

    def validate(self, attrs):
        validate_password(attrs['password'], User(**{k: v for k, v in attrs.items() if k != 'password'}))
        return attrs


class AdminSerializer(AccountSerializer):
    class Meta(AccountSerializer.Meta):
        extra_kwargs = {'username': {'validators': []}}

    def create(self, validated_data):
        return User.objects.create_user(
            **validated_data,
            user_type='admin',
            is_superuser=False,
            is_staff=False,
            is_active=False,
        )


class GuestSerializer(AccountSerializer):
    def create(self, validated_data):
        return User.objects.create_user(
            **validated_data,
            created_by=self.context['request'].user,
            user_type='guest',
            is_staff=False,
            is_superuser=False,
            is_active=False,
        )


class ListUserSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'user_type', 'first_name', 'last_name', 'status']

    def get_status(self, user):
        return 'Online' if user.is_online else 'Offline'
