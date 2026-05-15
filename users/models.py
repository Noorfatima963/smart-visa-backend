from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import random

class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(email, password, **extra_fields)

SIGNUP_SOURCE_CHOICES = [
    ('web',      'Web App'),
    ('mobile',   'Mobile App'),
    ('referral', 'Referral'),
    ('social',   'Social Media'),
]

SOCIAL_UTM_SOURCES = {'facebook', 'instagram', 'twitter', 'linkedin', 'tiktok', 'youtube', 'x'}


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    signup_source  = models.CharField(max_length=20, choices=SIGNUP_SOURCE_CHOICES, default='web')
    utm_source     = models.CharField(max_length=100, blank=True, default='')
    utm_medium     = models.CharField(max_length=100, blank=True, default='')
    utm_campaign   = models.CharField(max_length=100, blank=True, default='')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class EmailOTP(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='email_otp')
    otp = models.CharField(max_length=4)
    expires_at = models.DateTimeField()
    last_sent_at = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def can_resend(self):
        return (timezone.now() - self.last_sent_at).total_seconds() >= 30

    def refresh_otp(self):
        self.otp = f"{random.randint(1000, 9999)}"
        self.expires_at = timezone.now() + timezone.timedelta(minutes=10)
        self.last_sent_at = timezone.now()
        self.is_verified = False
        self.save()

    def __str__(self):
        return f"OTP for {self.user.email}"
