from django.contrib import admin

from .models import (
    Application
)

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'project', 'applicant', 'status', 'applied_at']
    list_filter = ['status']
    search_fields = ['id', 'project__title', 'applicant__email']
    readonly_fields = ['applied_at', 'updated_at']
    