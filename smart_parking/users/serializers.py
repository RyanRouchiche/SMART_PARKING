
from rest_framework import serializers

from users.models import User

class AdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = [ 'username', 'password','email','user_type', 'first_name', 'last_name' , 'is_superuser' , 'is_staff']
        
    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            user_type='admin',
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_superuser=True,
            is_staff=True,
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
    
class GuestSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password' , 'email', 'user_type', 'first_name', 'last_name', 'is_staff']
        
    def create(self, validated_data):
        user =User.objects.create_user(**validated_data)
        admin_uuid = self.context['request'].user.uuid  
        user.created_by = User.objects.get(uuid=admin_uuid)
        user.is_staff = True,
        user.is_superuser = False
        user.user_type = 'guest'
        user.save()
        return user
    
    
