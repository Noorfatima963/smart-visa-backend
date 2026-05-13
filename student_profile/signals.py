from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import StudentProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_student_profile(sender, instance, created, **kwargs):
    # Skip admin-panel created users (flag set in CustomUserAdmin.save_model)
    if created and not instance.is_superuser and not instance.is_staff:
        if not getattr(instance, '_skip_student_profile', False):
            StudentProfile.objects.create(user=instance)
