from rest_framework import serializers

from users.models import User


class AdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']

    def create(self, validated_data):
        return User.objects.create_user(
            **validated_data,
            user_type='admin',
            is_superuser=True,
            is_staff=True,
            is_active=False,
        )

class GuestSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name']

    def create(self, validated_data):
        return User.objects.create_user(
            **validated_data,
            created_by=self.context['request'].user,
            user_type='guest',
            is_staff=True,
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
