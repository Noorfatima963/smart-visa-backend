from rest_framework import serializers
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'password')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'phone_number': {'required': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(password=password, **validated_data)
        
        # Assign 'Student' group by default
        try:
            student_group = Group.objects.get(name='Student')
            user.groups.add(student_group)
        except Group.DoesNotExist:
            # Handle case where groups weren't created yet or logging
            pass
            
        user.is_active = False # Inactive until email verified
        user.save()
        return user

class EmailVerificationSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

class CustomTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                raise serializers.ValidationError({"detail": "No active account found with the given credentials"}, code='authorization')

            if not user.check_password(password):
                raise serializers.ValidationError({"detail": "No active account found with the given credentials"}, code='authorization')

            if not user.is_active:
                raise serializers.ValidationError({"detail": "User account is disabled."}, code='authorization')
        
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh = RefreshToken.for_user(user)

            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        else:
             raise serializers.ValidationError({"detail": "Must include 'email' and 'password'."}, code='authorization')
