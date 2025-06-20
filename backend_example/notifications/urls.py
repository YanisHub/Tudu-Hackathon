from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<uuid:pk>/', views.NotificationDetailView.as_view(), name='notification-detail'),
    path('mark-read/', views.MarkNotificationsReadView.as_view(), name='mark-notifications-read'),
    path('bulk-delete/', views.BulkDeleteNotificationsView.as_view(), name='bulk-delete-notifications'),
    path('count/', views.NotificationCountView.as_view(), name='notification-count'),
]