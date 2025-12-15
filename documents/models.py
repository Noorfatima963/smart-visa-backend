import uuid
import os
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

def validate_file_size(value):
    limit = 5 * 1024 * 1024  # 5 MB
    if value.size > limit:
        raise ValidationError('File too large. Size should not exceed 5 MiB.')

def user_document_path(instance, filename):
    """
    Generates a secure file path: documents/user_<uuid>/<doc_type>/<filename>
    """
    ext = filename.split('.')[-1]
    # Clean filename or use UUID to prevent overwrites/collisions
    new_filename = f"{instance.document_definition.slug}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join(
        f"documents/user_{instance.user.id}/",
        new_filename
    )

class DocumentDefinition(models.Model):
    """
    Master table: Defines what documents exist and their rules.
    Example: 'Passport', 'I-20', 'Blocked Account Proof'
    """
    class CountryChoice(models.TextChoices):
        ALL = 'ALL', _('Universal')
        USA = 'USA', _('United States')
        UK = 'UK', _('United Kingdom')
        GERMANY = 'DE', _('Germany')

    class PhaseChoice(models.TextChoices):
        ADMISSION = 'ADMISSION', _('University Admission')
        VISA = 'VISA', _('Visa Application')
        ENROLLMENT = 'ENROLLMENT', _('Enrollment/Arrival')

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, help_text="Unique key for frontend lookups")
    description = models.TextField(blank=True)
    
    # Logic gates
    country = models.CharField(
        max_length=10, 
        choices=CountryChoice.choices, 
        default=CountryChoice.ALL
    )
    phase = models.CharField(
        max_length=20, 
        choices=PhaseChoice.choices, 
        default=PhaseChoice.ADMISSION
    )
    is_mandatory = models.BooleanField(default=True)
    requires_original = models.BooleanField(default=False)
    
    # Metadata for reminders
    validity_months = models.PositiveIntegerField(
        null=True, blank=True, 
        help_text="Expected validity period (e.g., 6 months for bank statements)"
    )

    def __str__(self):
        return f"{self.name} ({self.get_country_display()})"


class UserDocument(models.Model):
    """
    The actual record of a user's uploaded document.
    """
    class StatusChoice(models.TextChoices):
        MISSING = 'MISSING', _('Missing / Not Started')
        PENDING = 'PENDING', _('Pending Review')
        VERIFIED = 'VERIFIED', _('Verified')
        REJECTED = 'REJECTED', _('Rejected')
        EXPIRED = 'EXPIRED', _('Expired')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    document_definition = models.ForeignKey(
        DocumentDefinition, 
        on_delete=models.PROTECT,
        related_name='user_instances'
    )
    
    # File Management
    file = models.FileField(
        upload_to=user_document_path,
        null=True, blank=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']),
            validate_file_size
        ]
    )
    
    # Workflow
    status = models.CharField(
        max_length=20, 
        choices=StatusChoice.choices, 
        default=StatusChoice.MISSING
    )
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Auditing
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_documents'
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    # Critical Dates (For Visa Logic)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'document_definition')
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'expiry_date']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.document_definition.name}"

    @property
    def is_valid_document(self):
        """Helper to check if document is verified and not expired"""
        from django.utils import timezone
        if self.status != self.StatusChoice.VERIFIED:
            return False
        if self.expiry_date and self.expiry_date < timezone.now().date():
            return False
        return True
