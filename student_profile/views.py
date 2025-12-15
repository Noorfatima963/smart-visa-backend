from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import StudentProfile, Education, LanguageTest, StudentTravelHistory, StudentFinancialProfile
from .serializers import (
    StudentProfileSerializer, 
    EducationSerializer, 
    LanguageTestSerializer, 
    StudentTravelHistorySerializer, 
    StudentFinancialProfileSerializer
)

class StudentProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the authenticated user's profile.
    Created automatically if it doesn't exist.
    """
    serializer_class = StudentProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, created = StudentProfile.objects.get_or_create(user=self.request.user)
        return profile

class EducationListCreateView(generics.ListCreateAPIView):
    """
    List education history or add a new education record.
    """
    serializer_class = EducationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # We need the profile to exist
        profile, _ = StudentProfile.objects.get_or_create(user=self.request.user)
        return Education.objects.filter(profile=profile)

    def perform_create(self, serializer):
        profile, _ = StudentProfile.objects.get_or_create(user=self.request.user)
        serializer.save(profile=profile)

class EducationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Update or delete a specific education record.
    """
    serializer_class = EducationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        profile, _ = StudentProfile.objects.get_or_create(user=self.request.user)
        return Education.objects.filter(profile=profile)

class LanguageTestListCreateView(generics.ListCreateAPIView):
    serializer_class = LanguageTestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        profile, _ = StudentProfile.objects.get_or_create(user=self.request.user)
        return LanguageTest.objects.filter(profile=profile)

    def perform_create(self, serializer):
        profile, _ = StudentProfile.objects.get_or_create(user=self.request.user)
        serializer.save(profile=profile)

class LanguageTestDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LanguageTestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        profile, _ = StudentProfile.objects.get_or_create(user=self.request.user)
        return LanguageTest.objects.filter(profile=profile)

class TravelHistoryListCreateView(generics.ListCreateAPIView):
    serializer_class = StudentTravelHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        profile, _ = StudentProfile.objects.get_or_create(user=self.request.user)
        return StudentTravelHistory.objects.filter(profile=profile)

    def perform_create(self, serializer):
        profile, _ = StudentProfile.objects.get_or_create(user=self.request.user)
        serializer.save(profile=profile)

class TravelHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StudentTravelHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        profile, _ = StudentProfile.objects.get_or_create(user=self.request.user)
        return StudentTravelHistory.objects.filter(profile=profile)

class FinancialProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = StudentFinancialProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = StudentProfile.objects.get_or_create(user=self.request.user)
        financial_profile, created = StudentFinancialProfile.objects.get_or_create(profile=profile)
        return financial_profile
