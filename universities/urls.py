from django.urls import path
from . import views

urlpatterns = [
    # University list & detail
    path('', views.UniversityListView.as_view(), name='university-list'),
    path('<int:pk>/', views.UniversityDetailView.as_view(), name='university-detail'),

    # Programs for a specific university
    path('<int:pk>/programs/', views.UniversityProgramListView.as_view(), name='university-programs'),

    # Cross-university program search
    path('programs/search/', views.ProgramSearchView.as_view(), name='program-search'),
]
