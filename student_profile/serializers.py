from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (Education, LanguageTest, StudentFinancialProfile,
                     StudentProfile, StudentTravelHistory, AdminNote)

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


class AdminStudentSummarySerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    display_name = serializers.SerializerMethodField()
    latest_program = serializers.SerializerMethodField()
    ielts_score = serializers.SerializerMethodField()
    savings = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    readiness_score = serializers.ReadOnlyField()

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'display_name', 'first_name', 'last_name', 'email',
            'target_country', 'target_degree_type', 'nationality',
            'readiness_score', 'latest_program', 'ielts_score', 'savings',
            'status', 'created_at',
        ]

    def get_display_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name or obj.user.email.split('@')[0]

    def get_latest_program(self, obj):
        edu = obj.education_history.order_by('-end_date').first()
        return edu.degree_title if edu else None

    def get_ielts_score(self, obj):
        test = obj.test_scores.filter(test_type='ielts').first()
        return float(test.overall_score) if test else None

    def get_savings(self, obj):
        fin = getattr(obj, 'financial_profile', None)
        if fin and fin.approx_savings:
            return float(fin.approx_savings)
        return 0

    def get_status(self, obj):
        score = obj.readiness_score
        if score >= 80:
            return 'visa_approved'
        elif score >= 60:
            return 'in_review'
        elif score >= 30:
            return 'in_progress'
        return 'incomplete'


class AdminNoteSerializer(serializers.ModelSerializer):
    admin_name = serializers.SerializerMethodField()

    class Meta:
        model = AdminNote
        fields = ['id', 'content', 'admin_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'admin_name', 'created_at', 'updated_at']

    def get_admin_name(self, obj):
        name = f"{obj.admin_user.first_name} {obj.admin_user.last_name}".strip()
        return name or obj.admin_user.email
