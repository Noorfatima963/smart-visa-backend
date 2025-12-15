from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from .models import DocumentDefinition, UserDocument
from .serializers import DocumentDefinitionSerializer, UserDocumentSerializer

class DocumentDefinitionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    List available document types.
    Filterable by country and phase.
    """
    queryset = DocumentDefinition.objects.all()
    serializer_class = DocumentDefinitionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        country = self.request.query_params.get('country')
        phase = self.request.query_params.get('phase')
        
        if country:
            # Include 'ALL' (Universal) docs + specific country docs
            queryset = queryset.filter(country__in=['ALL', country])
        
        if phase:
            queryset = queryset.filter(phase=phase)
            
        return queryset

class UserDocumentViewSet(viewsets.ModelViewSet):
    """
    Manage user's uploaded documents.
    """
    serializer_class = UserDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def get_queryset(self):
        return UserDocument.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'], url_path='upload')
    def upload_document(self, request):
        """
        Custom endpoint for uploading if standard create isn't enough.
        Actually standard create should handle it if 'definition_slug' is passed.
        Keeping this just in case we need special logic, but relying on standard 'create' is better.
        """
        return super().create(request)
