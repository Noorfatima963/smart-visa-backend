from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DocumentDefinitionViewSet,
    UserDocumentViewSet,
    AdminStudentDocumentsView,
    AdminDocumentReviewView,
    AdminRequestDocumentView,
)

router = DefaultRouter()
router.register(r'definitions', DocumentDefinitionViewSet, basename='document-definitions')
router.register(r'', UserDocumentViewSet, basename='user-documents')

urlpatterns = [
    # Admin routes — must be before include(router.urls)
    path('admin/student/<int:profile_pk>/',          AdminStudentDocumentsView.as_view(),  name='admin-student-documents'),
    path('admin/student/<int:profile_pk>/request/',  AdminRequestDocumentView.as_view(),   name='admin-request-document'),
    path('admin/<uuid:pk>/review/',                  AdminDocumentReviewView.as_view(),    name='admin-document-review'),
    path('', include(router.urls)),
]
