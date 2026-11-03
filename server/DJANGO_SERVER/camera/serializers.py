import os
import re

from django.conf import settings
from rest_framework import serializers

from camera.models import Camera
from camera.sources import UnsafeSource, check_camera_url, is_url


def camera_file(parking, value):
    root = os.path.realpath(os.path.join(settings.CAMERA_MEDIA_ROOT, str(parking.id)))
    path = os.path.realpath(os.path.join(root, value))
    if os.path.commonpath([path, root]) != root or path == root:
        raise serializers.ValidationError(f'Video files must be inside the parking folder {root}')
    return path


class CameraSerializer(serializers.ModelSerializer):
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Camera
        fields = ['id', 'area', 'path', 'is_active', 'ref', 'capture_mode', 'stream_url']

    def validate_path(self, value):
        if not is_url(value):
            return camera_file(self.context['parking'], value)
        try:
            check_camera_url(value)
        except UnsafeSource as e:
            raise serializers.ValidationError(str(e))
        return value

    def get_is_active(self, obj):
        return self.context.get('health', {}).get(obj.path, False)


MAX_COORD = 8192
MAX_SPOTS = 500
MAX_AREAS = 50


class AreaSerializer(serializers.Serializer):
    area = serializers.RegexField(r"^\d{1,4}$")
    coordinates = serializers.DictField(
        child=serializers.ListField(
            child=serializers.ListField(
                child=serializers.IntegerField(min_value=0, max_value=MAX_COORD),
                min_length=2,
                max_length=2
            ),
            min_length=4,
            max_length=4
        )
    )

    def validate_coordinates(self, value):
        if len(value) > MAX_SPOTS:
            raise serializers.ValidationError(f"At most {MAX_SPOTS} spots per area")
        invalid = [name for name in value if not re.fullmatch(r"[\w -]{1,64}", name)]
        if invalid:
            raise serializers.ValidationError(f"Invalid spot names: {invalid}")
        return value
