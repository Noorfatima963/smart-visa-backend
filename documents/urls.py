from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DocumentDefinitionViewSet, UserDocumentViewSet

router = DefaultRouter()
router.register(r'definitions', DocumentDefinitionViewSet, basename='document-definitions')
router.register(r'', UserDocumentViewSet, basename='user-documents')

urlpatterns = [
    path('', include(router.urls)),
]
