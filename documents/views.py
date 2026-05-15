from rest_framework import viewsets, permissions, status as http_status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import DocumentDefinition, UserDocument
from .serializers import DocumentDefinitionSerializer, UserDocumentSerializer


class IsAdminGroupUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_staff or
             request.user.groups.filter(name='Admin').exists())
        )


class DocumentDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DocumentDefinition.objects.all()
    serializer_class = DocumentDefinitionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        country = self.request.query_params.get('country')
        phase = self.request.query_params.get('phase')
        if country:
            queryset = queryset.filter(country__in=['ALL', country])
        if phase:
            queryset = queryset.filter(phase=phase)
        return queryset


class UserDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = UserDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_queryset(self):
        return UserDocument.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='upload')
    def upload_document(self, request):
        return super().create(request)


class AdminStudentDocumentsView(generics.ListAPIView):
    """Admin: list all documents uploaded by a student (identified by profile pk)."""
    serializer_class = UserDocumentSerializer
    permission_classes = [IsAuthenticated, IsAdminGroupUser]

    def get_queryset(self):
        from student_profile.models import StudentProfile
        profile = get_object_or_404(StudentProfile, pk=self.kwargs['profile_pk'])
        return (
            UserDocument.objects
            .filter(user=profile.user)
            .select_related('document_definition')
            .order_by('document_definition__phase', 'document_definition__name')
        )


class AdminDocumentReviewView(APIView):
    """Admin: set a document's status to VERIFIED, REJECTED, or PENDING."""
    permission_classes = [IsAuthenticated, IsAdminGroupUser]

    def patch(self, request, pk):
        doc = get_object_or_404(UserDocument, pk=pk)
        new_status = request.data.get('status', '').upper()
        rejection_reason = request.data.get('rejection_reason', '')

        if new_status not in ('VERIFIED', 'REJECTED', 'PENDING'):
            return Response(
                {'detail': 'status must be VERIFIED, REJECTED, or PENDING'},
                status=http_status.HTTP_400_BAD_REQUEST,
            )

        doc.status = new_status
        doc.rejection_reason = rejection_reason if new_status == 'REJECTED' else ''
        if new_status == 'VERIFIED':
            doc.verified_by = request.user
            doc.verified_at = timezone.now()
        doc.save(update_fields=['status', 'rejection_reason', 'verified_by', 'verified_at'])

        return Response(UserDocumentSerializer(doc, context={'request': request}).data)


class AdminRequestDocumentView(APIView):
    """
    GET  /api/documents/admin/student/<profile_pk>/request/
        — returns all DocumentDefinitions, annotated with whether the student
          already has a UserDocument for each one.

    POST /api/documents/admin/student/<profile_pk>/request/
        — creates a UserDocument(status=MISSING) so the student sees it as
          a pending request in their document checklist.
    """
    permission_classes = [IsAuthenticated, IsAdminGroupUser]

    def get(self, request, profile_pk):
        from student_profile.models import StudentProfile
        profile = get_object_or_404(StudentProfile, pk=profile_pk)
        country = profile.target_country or 'ALL'
        definitions = DocumentDefinition.objects.filter(country__in=['ALL', country]).order_by('phase', 'name')
        existing_def_ids = set(
            UserDocument.objects.filter(user=profile.user).values_list('document_definition_id', flat=True)
        )
        data = []
        for d in definitions:
            row = DocumentDefinitionSerializer(d).data
            row['already_requested'] = d.id in existing_def_ids
            data.append(row)
        return Response(data)

    def post(self, request, profile_pk):
        from student_profile.models import StudentProfile
        profile = get_object_or_404(StudentProfile, pk=profile_pk)
        definition_id = request.data.get('definition_id')
        if not definition_id:
            return Response({'detail': 'definition_id is required.'}, status=http_status.HTTP_400_BAD_REQUEST)
        definition = get_object_or_404(DocumentDefinition, pk=definition_id)
        doc, created = UserDocument.objects.get_or_create(
            user=profile.user,
            document_definition=definition,
            defaults={'status': UserDocument.StatusChoice.MISSING},
        )
        if not created:
            return Response({'detail': 'Document already requested or uploaded by this student.'}, status=http_status.HTTP_400_BAD_REQUEST)
        return Response(UserDocumentSerializer(doc, context={'request': request}).data, status=http_status.HTTP_201_CREATED)
