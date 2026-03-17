from django.urls import path
from . import views

urlpatterns = [
    # ── Assessment lifecycle ───────────────────────────────────────────────────
    path('run/',                 views.RunAssessmentView.as_view(),    name='assessment-run'),
    path('',                     views.AssessmentHistoryView.as_view(),name='assessment-history'),
    path('<int:pk>/',            views.AssessmentDetailView.as_view(), name='assessment-detail'),
    path('<int:pk>/delete/',     views.AssessmentDeleteView.as_view(), name='assessment-delete'),

    # ── Cost estimator (standalone) ────────────────────────────────────────────
    # Get full cost breakdown for a single program
    # GET /api/assessments/cost/<program_id>/?country=USA
    path('cost/<int:program_id>/', views.ProgramCostEstimateView.as_view(), name='program-cost-estimate'),

    # Get fixed visa + insurance info for a country
    # GET /api/assessments/cost-info/USA/
    path('cost-info/<str:country>/', views.CountryCostInfoView.as_view(), name='country-cost-info'),
]