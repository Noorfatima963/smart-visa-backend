from rest_framework import serializers
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from .models import CustomUser

class UserRegistrationSerializer(serializers.ModelSerializer):
    password    = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    utm_source  = serializers.CharField(required=False, allow_blank=True, default='')
    utm_medium  = serializers.CharField(required=False, allow_blank=True, default='')
    utm_campaign = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'password',
                  'utm_source', 'utm_medium', 'utm_campaign')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'phone_number': {'required': False, 'allow_null': True, 'allow_blank': True},
        }

    def create(self, validated_data):
        from .models import SOCIAL_UTM_SOURCES
        password     = validated_data.pop('password')
        utm_source   = validated_data.get('utm_source', '').lower()
        utm_medium   = validated_data.get('utm_medium', '').lower()

        if utm_medium == 'referral' or utm_source == 'referral':
            source = 'referral'
        elif utm_source in SOCIAL_UTM_SOURCES or utm_medium == 'social':
            source = 'social'
        else:
            source = 'web'

        validated_data['signup_source'] = source
        user = CustomUser.objects.create_user(password=password, **validated_data)

        try:
            student_group = Group.objects.get(name='Student')
            user.groups.add(student_group)
        except Group.DoesNotExist:
            pass

        user.is_active = False
        user.save()
        return user

class EmailVerificationSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()


class MobileRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'password')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'phone_number': {'required': False, 'allow_null': True, 'allow_blank': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data['signup_source'] = 'mobile'
        user = CustomUser.objects.create_user(password=password, **validated_data)
        try:
            student_group = Group.objects.get(name='Student')
            user.groups.add(student_group)
        except Group.DoesNotExist:
            pass
        user.is_active = False
        user.save()
        return user


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=4, min_length=4)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

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
            groups = list(user.groups.values_list('name', flat=True))

            return {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'access_expires': refresh.access_token.lifetime.total_seconds(),
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'role': groups[0] if groups else 'Student',
            }
        else:
             raise serializers.ValidationError({"detail": "Must include 'email' and 'password'."}, code='authorization')
