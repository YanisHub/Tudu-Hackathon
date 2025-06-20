from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['recipient__email', 'message']
    readonly_fields = ['recipient', 'notification_type', 'message', 'content_type', 'object_id', 'created_at']
    date_hierarchy = 'created_at'
