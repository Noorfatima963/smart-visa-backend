from django.contrib import admin
from .models import DocumentDefinition, UserDocument

@admin.register(DocumentDefinition)
class DocumentDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'phase', 'is_mandatory')
    list_filter = ('country', 'phase', 'is_mandatory')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(UserDocument)
class UserDocumentAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'document_name', 'status', 'issue_date', 'expiry_date')
    list_filter = ('status', 'document_definition__country', 'document_definition__phase')
    search_fields = ('user__email', 'document_definition__name')
    readonly_fields = ('created_at', 'updated_at')

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'

    def document_name(self, obj):
        return obj.document_definition.name
    document_name.short_description = 'Document'
