from rest_framework import serializers
from camera.models import Camera
import cv2

class CameraSerializer(serializers.ModelSerializer):
    is_active = serializers.SerializerMethodField()
    class Meta:
        model = Camera
        fields = ['id', 'area', 'path', 'is_active', 'ref']

    def get_is_active(self, obj):
        cap = cv2.VideoCapture(obj.path)
        ret, _ = cap.read()
        cap.release()
        return ret
