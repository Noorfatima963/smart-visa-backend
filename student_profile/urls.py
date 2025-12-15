from django.urls import path
from .views import (
    StudentProfileView, 
    EducationListCreateView, 
    EducationDetailView,
    LanguageTestListCreateView,
    LanguageTestDetailView,
    TravelHistoryListCreateView,
    TravelHistoryDetailView,
    FinancialProfileView
)

urlpatterns = [
    path('', StudentProfileView.as_view(), name='student-profile'),
    path('education/', EducationListCreateView.as_view(), name='education-list-create'),
    path('education/<int:pk>/', EducationDetailView.as_view(), name='education-detail'),
    path('language-tests/', LanguageTestListCreateView.as_view(), name='language-test-list-create'),
    path('language-tests/<int:pk>/', LanguageTestDetailView.as_view(), name='language-test-detail'),
    path('travel-history/', TravelHistoryListCreateView.as_view(), name='travel-history-list-create'),
    path('travel-history/<int:pk>/', TravelHistoryDetailView.as_view(), name='travel-history-detail'),
    path('financial/', FinancialProfileView.as_view(), name='financial-profile'),
]
