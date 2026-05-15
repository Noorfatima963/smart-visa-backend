from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    RegisterView, VerifyEmailView, CustomTokenObtainPairView,
    MobileRegisterView, MobileVerifyOTPView, ResendOTPView,
    AdminStatsView, AdminStudentListView, AdminStudentDetailView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Mobile OTP flow
    path('mobile/register/', MobileRegisterView.as_view(), name='mobile_register'),
    path('mobile/verify-otp/', MobileVerifyOTPView.as_view(), name='mobile_verify_otp'),
    path('mobile/resend-otp/', ResendOTPView.as_view(), name='mobile_resend_otp'),
    # Admin
    path('admin/stats/', AdminStatsView.as_view(), name='admin_stats'),
    path('admin/students/', AdminStudentListView.as_view(), name='admin_students'),
    path('admin/students/<int:pk>/', AdminStudentDetailView.as_view(), name='admin_student_detail'),
]
