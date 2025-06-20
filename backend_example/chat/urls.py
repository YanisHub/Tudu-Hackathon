from django.urls import path

from . import views

urlpatterns = [
    # Sessions de chat
    path('sessions/', views.ChatSessionList.as_view(), name='chat-session-list'),
    path('sessions/<uuid:pk>/', views.ChatSessionDetail.as_view(), name='chat-session-detail'),
    
    # Messages d'une session spécifique
    path('sessions/<uuid:chat_session_id>/messages/', views.ChatMessageList.as_view(), name='chat-message-list'),
    path('sessions/<uuid:chat_session_id>/upload-attachment/', views.UploadAttachment.as_view(), name='upload-attachment'),
]