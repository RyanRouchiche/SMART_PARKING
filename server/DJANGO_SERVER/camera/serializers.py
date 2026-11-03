import os

from django.conf import settings
from rest_framework import serializers

from camera.models import Camera
from camera.sources import UnsafeSource, check_camera_url, is_url, open_source


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
        cap = open_source(obj.path)
        ret, _ = cap.read()
        cap.release()
        return ret
