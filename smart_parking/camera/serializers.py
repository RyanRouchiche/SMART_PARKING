from rest_framework import serializers
from camera.models import Camera
import cv2
import os

class CameraSerializer(serializers.ModelSerializer):
    is_active = serializers.SerializerMethodField()
    print(is_active)
    class Meta:
        model = Camera
        fields = ['id','area' , 'path' , 'is_active' , 'ref']
    def get_is_active(self, obj):
        # cap  = cv2.VideoCapture(obj.path)
        # ret  , frame = cap.read()
        # if ret:
        #     cap.release()
        #     return True
        # else:
        #     cap.release()
        #     return False
        filepath = os.path.join(obj.path)
        print(filepath)
        return os.path.exists(filepath)