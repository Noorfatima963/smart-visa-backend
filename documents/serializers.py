from rest_framework import serializers
from .models import DocumentDefinition, UserDocument

class DocumentDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentDefinition
        fields = [
            'slug', 'name', 'country', 'phase', 
            'is_mandatory', 'requires_original', 'description',
            'validity_months'
        ]

class UserDocumentSerializer(serializers.ModelSerializer):
    definition_slug = serializers.CharField(write_only=True)
    document_name = serializers.CharField(source='document_definition.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = UserDocument
        fields = [
            'id', 'definition_slug', 'document_name', 'file', 
            'status', 'status_display', 'rejection_reason',
            'issue_date', 'expiry_date', 'verified_at', 'updated_at',
            'ai_status', 'ai_extracted_data', 'ai_rejection_reason', 'ai_confidence_score'
        ]
        read_only_fields = ['id', 'status', 'rejection_reason', 'verified_at', 'updated_at', 
                            'ai_status', 'ai_extracted_data', 'ai_rejection_reason', 'ai_confidence_score']

    def create(self, validated_data):
        slug = validated_data.pop('definition_slug')
        user = self.context['request'].user
        
        try:
            definition = DocumentDefinition.objects.get(slug=slug)
        except DocumentDefinition.DoesNotExist:
            raise serializers.ValidationError({"definition_slug": "Invalid document slug."})
            
        # Update existing or create new
        doc, created = UserDocument.objects.update_or_create(
            user=user,
            document_definition=definition,
            defaults=validated_data
        )
        
        # If updating, reset status to PENDING if it was REJECTED/MISSING
        if not created and doc.status in ['REJECTED', 'MISSING']:
            doc.status = 'PENDING'
            doc.save()
            
        # Trigger Background AI Processing if a file is present
        if doc.file:
            from .ai_service import submit_ai_verification
            submit_ai_verification(doc)
            
        return doc
