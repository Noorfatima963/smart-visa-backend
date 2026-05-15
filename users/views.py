from rest_framework import generics, status, views
from django.db.models import Q
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from datetime import timedelta
from .serializers import (
    UserRegistrationSerializer, EmailVerificationSerializer,
    CustomTokenObtainPairSerializer, MobileRegisterSerializer,
    VerifyOTPSerializer, ResendOTPSerializer,
)
from .utils import send_verification_email, generate_otp, send_otp_email
from .models import EmailOTP, SIGNUP_SOURCE_CHOICES

User = get_user_model()


class IsAdminGroupUser(BasePermission):
    """Allows access to users in the 'Admin' group or with is_staff=True."""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_staff or
             request.user.groups.filter(name='Admin').exists())
        )

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        send_verification_email(user, self.request)

class VerifyEmailView(views.APIView):
    permission_classes = (AllowAny,)
    serializer_class = EmailVerificationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            uid = serializer.validated_data.get('uid')
            token = serializer.validated_data.get('token')

            try:
                uid = force_str(urlsafe_base64_decode(uid))
                user = User.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                user = None

            if user is not None and default_token_generator.check_token(user, token):
                user.is_active = True
                user.save()
                return Response({'message': 'Email verified successfully! You can now login.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid verification link or expired.'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class MobileRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = MobileRegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        otp_code = generate_otp()
        EmailOTP.objects.create(
            user=user,
            otp=otp_code,
            expires_at=timezone.now() + timezone.timedelta(minutes=10),
        )
        try:
            send_otp_email(user, otp_code)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"OTP email failed for {user.email}: {e}")
        return Response(
            {'message': 'Account created. Check your email for the 4-digit verification code.'},
            status=status.HTTP_201_CREATED,
        )


class MobileVerifyOTPView(views.APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']

        try:
            user = User.objects.get(email=email)
            otp_obj = EmailOTP.objects.get(user=user)
        except (User.DoesNotExist, EmailOTP.DoesNotExist):
            return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.is_verified:
            return Response({'error': 'OTP already used.'}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.is_expired():
            return Response({'error': 'OTP has expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.otp != otp:
            return Response({'error': 'Incorrect OTP. Please try again.'}, status=status.HTTP_400_BAD_REQUEST)

        otp_obj.is_verified = True
        otp_obj.save()
        user.is_active = True
        user.save()

        return Response({'message': 'Email verified successfully! You can now sign in.'}, status=status.HTTP_200_OK)


class ResendOTPView(views.APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
            otp_obj = EmailOTP.objects.get(user=user)
        except (User.DoesNotExist, EmailOTP.DoesNotExist):
            return Response({'error': 'Invalid request.'}, status=status.HTTP_400_BAD_REQUEST)

        if otp_obj.is_verified:
            return Response({'error': 'Email is already verified.'}, status=status.HTTP_400_BAD_REQUEST)

        if not otp_obj.can_resend():
            seconds_left = int(30 - (timezone.now() - otp_obj.last_sent_at).total_seconds())
            return Response(
                {'error': f'Please wait {seconds_left} seconds before requesting a new OTP.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        otp_obj.refresh_otp()
        send_otp_email(user, otp_obj.otp)

        return Response({'message': 'A new OTP has been sent to your email.'}, status=status.HTTP_200_OK)


class AdminStatsView(views.APIView):
    permission_classes = [IsAuthenticated, IsAdminGroupUser]

    def get(self, request):
        from assessments.models import VisaAssessment
        from student_profile.models import StudentProfile

        total_users     = User.objects.filter(is_active=True).count()
        total_profiles  = StudentProfile.objects.count()
        approved        = VisaAssessment.objects.filter(status='completed').count()

        # Traffic sources — count per signup_source
        traffic_sources = {
            source: User.objects.filter(signup_source=source).count()
            for source, _ in SIGNUP_SOURCE_CHOICES
        }

        # Last 7 days signups for chart
        today = timezone.now().date()
        weekly_signups = []
        for offset in range(6, -1, -1):
            day = today - timedelta(days=offset)
            count = User.objects.filter(date_joined__date=day).count()
            weekly_signups.append({
                'day':   day.strftime('%a'),
                'date':  day.isoformat(),
                'count': count,
            })

        return Response({
            'total_users':         total_users,
            'total_profiles':      total_profiles,
            'approved_assessments': approved,
            'revenue':             0,
            'traffic_sources':     traffic_sources,
            'weekly_signups':      weekly_signups,
        })


class AdminStudentListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsAdminGroupUser]

    def get_serializer_class(self):
        from student_profile.serializers import AdminStudentSummarySerializer
        return AdminStudentSummarySerializer

    def get_queryset(self):
        from student_profile.models import StudentProfile
        qs = StudentProfile.objects.select_related(
            'user', 'financial_profile'
        ).prefetch_related('education_history', 'test_scores')

        search = self.request.query_params.get('search', '').strip()
        country = self.request.query_params.get('country', '').strip()

        if search:
            qs = qs.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(user__email__icontains=search)
            )
        if country:
            qs = qs.filter(target_country__icontains=country)

        return qs.order_by('-created_at')


class AdminStudentDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated, IsAdminGroupUser]

    def get_serializer_class(self):
        from student_profile.serializers import StudentProfileSerializer
        return StudentProfileSerializer

    def get_queryset(self):
        from student_profile.models import StudentProfile
        return StudentProfile.objects.select_related(
            'user', 'financial_profile'
        ).prefetch_related('education_history', 'test_scores', 'travel_history')
