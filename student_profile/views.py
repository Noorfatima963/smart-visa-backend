from rest_framework import generics, permissions, status
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import StudentProfile, Education, LanguageTest, StudentTravelHistory, StudentFinancialProfile, AdminNote
from .serializers import (
    StudentProfileSerializer,
    EducationSerializer,
    LanguageTestSerializer,
    StudentTravelHistorySerializer,
    StudentFinancialProfileSerializer,
    AdminNoteSerializer,
)


class IsAdminGroupUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            (request.user.is_staff or request.user.groups.filter(name='Admin').exists())
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


class AdminNotesView(APIView):
    """GET / POST admin notes for a student profile."""
    permission_classes = [IsAuthenticated, IsAdminGroupUser]

    def get(self, request, profile_pk):
        profile = get_object_or_404(StudentProfile, pk=profile_pk)
        notes = AdminNote.objects.filter(profile=profile)
        return Response(AdminNoteSerializer(notes, many=True).data)

    def post(self, request, profile_pk):
        profile = get_object_or_404(StudentProfile, pk=profile_pk)
        content = request.data.get('content', '').strip()
        if not content:
            return Response({'detail': 'Content is required.'}, status=status.HTTP_400_BAD_REQUEST)
        note = AdminNote.objects.create(profile=profile, admin_user=request.user, content=content)
        return Response(AdminNoteSerializer(note).data, status=status.HTTP_201_CREATED)


class AdminNoteDetailView(APIView):
    """DELETE a single admin note."""
    permission_classes = [IsAuthenticated, IsAdminGroupUser]

    def delete(self, request, profile_pk, note_pk):
        profile = get_object_or_404(StudentProfile, pk=profile_pk)
        note = get_object_or_404(AdminNote, pk=note_pk, profile=profile)
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
