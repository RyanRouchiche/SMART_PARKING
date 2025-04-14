
from rest_framework import serializers

from users.models import User , auth
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


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
        user.is_active =  False
        user.save()
        return user
    
class GuestSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password' , 'email', 'user_type', 'first_name', 'last_name', 'is_staff']
        
    def create(self, validated_data):
        user =User.objects.create_user(**validated_data)
        admin_uuid = self.context['request'].session.get('id')
        user.created_by = User.objects.get(id=admin_uuid)
        user.is_staff = True
        user.is_superuser = False
        user.user_type = 'guest'
        user.is_active =  False
        user.save()
        return user
    
    

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        
        data['user'] = {
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.user_type,
            'id': str(self.user.id)
        }

        return data
    
class ListUserSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'user_type', 'first_name', 'last_name' , 'status']
        
    def get_status(self, user):
            try : 
                token = auth.objects.filter(user_id=user , is_revoked=False).first()
                if token:
                    return 'Online'
                else:
                    return 'Offline'
            except auth.DoesNotExist:
                return 'Offline'
                


