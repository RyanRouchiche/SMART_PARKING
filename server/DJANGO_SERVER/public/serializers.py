from rest_framework import serializers

from .models import OwnerRequest

PHONE = r'^\+?[\d\s.-]{9,20}$'


class OwnerRequestSerializer(serializers.ModelSerializer):
    phone = serializers.RegexField(PHONE)
    consent = serializers.BooleanField(write_only=True)

    class Meta:
        model = OwnerRequest
        fields = ['name', 'company', 'phone', 'email', 'parking_name', 'address', 'capacity', 'cameras', 'fiber', 'message', 'language', 'consent']

    def validate_consent(self, value):
        if not value:
            raise serializers.ValidationError('Consent is required.')
        return value

    def create(self, validated_data):
        validated_data.pop('consent')
        return super().create(validated_data)


class ContactSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    email = serializers.EmailField()
    message = serializers.CharField(max_length=4000)


class DeviceSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=512)
    platform = serializers.ChoiceField(choices=['android', 'ios'], required=False)


class FavoriteSerializer(serializers.Serializer):
    notify = serializers.BooleanField(default=False)
