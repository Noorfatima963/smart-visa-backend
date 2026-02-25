from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (Education, LanguageTest, StudentFinancialProfile,
                     StudentProfile, StudentTravelHistory)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number')


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = '__all__'
        read_only_fields = ('profile',)


class LanguageTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LanguageTest
        fields = '__all__'
        read_only_fields = ('profile',)


class StudentTravelHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentTravelHistory
        fields = '__all__'
        read_only_fields = ('profile',)


class StudentFinancialProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentFinancialProfile
        fields = '__all__'
        read_only_fields = ('profile',)


class StudentProfileSerializer(serializers.ModelSerializer):
    education_history = EducationSerializer(many=True, read_only=True)
    test_scores = LanguageTestSerializer(many=True, read_only=True)
    travel_history = StudentTravelHistorySerializer(
        many=True, read_only=True)
    financial_profile = StudentFinancialProfileSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    readiness_score = serializers.ReadOnlyField()
    readiness_next_step = serializers.ReadOnlyField()

    class Meta:
        model = StudentProfile
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'readiness_score', 'readiness_next_step')
