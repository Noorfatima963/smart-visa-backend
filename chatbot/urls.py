from django.urls import path
from . import views

urlpatterns = [
    path('message/',     views.ChatMessageView.as_view(),     name='chat-message'),
    path('suggestions/', views.ChatSuggestionsView.as_view(), name='chat-suggestions'),
]
