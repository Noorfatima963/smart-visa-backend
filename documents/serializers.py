from rest_framework import serializers
from .models import DocumentDefinition, UserDocument

class DocumentDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentDefinition
        fields = [
            'id', 'slug', 'name', 'country', 'phase', 
            'is_mandatory', 'requires_original', 'requires_ai_extraction', 
            'description', 'validity_months'
        ]

class UserDocumentSerializer(serializers.ModelSerializer):
    definition_slug = serializers.CharField(write_only=True)
    slug = serializers.CharField(source='document_definition.slug', read_only=True)
    document_name = serializers.CharField(source='document_definition.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = UserDocument
        fields = [
            'id', 'definition_slug', 'slug', 'document_name', 'file', 
            'status', 'status_display', 'rejection_reason',
            'issue_date', 'expiry_date', 'verified_at', 'updated_at',
            'ai_status', 'ai_extracted_data', 'ai_rejection_reason', 'ai_confidence_score'
        ]
        read_only_fields = ['id', 'status', 'rejection_reason', 'verified_at', 'updated_at', 
                            'ai_status', 'ai_extracted_data', 'ai_rejection_reason', 'ai_confidence_score']

    def to_representation(self, instance):
        # Ensure definition_slug is present in the output for frontend compatibility
        ret = super().to_representation(instance)
        ret['definition_slug'] = instance.document_definition.slug
        return ret

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
        
        # If updating or creating, make sure it's PENDING
        if created or doc.status in ['REJECTED', 'MISSING']:
            doc.status = 'PENDING'
            doc.save()
            
        # Trigger Background AI Processing if a file is present AND required
        if doc.file and definition.requires_ai_extraction:
            from .ai_service import submit_ai_verification
            submit_ai_verification(doc)
        elif doc.file:
            # If AI is not required, mark as PENDING (or VERIFIED if we trust uploads)
            # For now, let's mark as VERIFIED immediately if no AI check is needed
            doc.status = 'VERIFIED'
            doc.save()
            
        return doc
