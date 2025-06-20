from django.contrib import admin
from .models import (
    Project,
    ProjectAttachment
)

class ProjectAttachmentInline(admin.TabularInline):
    model = ProjectAttachment
    extra = 1
    fields = ('file', 'file_name', 'file_size', 'uploaded_by', 'description')
    readonly_fields = ('created_at',)
    can_delete = True
    show_change_link = True

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'collaborator', 'status', 'budget', 'deadline', 'created_at')
    list_filter = ('status', 'created_at', 'deadline')
    search_fields = ('title', 'description', 'owner__email', 'owner__username', 'collaborator__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    date_hierarchy = 'deadline'
    ordering = ('-created_at',)
    raw_id_fields = ('owner', 'collaborator')
    filter_horizontal = ('expertise_required',)
    
    fieldsets = (
        (None, {
            'fields': ('id', 'title', 'description')
        }),
        ('People', {
            'fields': ('owner', 'collaborator')
        }),
        ('Project Details', {
            'fields': ('status', 'expertise_required', 'estimated_hours', 'budget', 'deadline')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ProjectAttachmentInline]

@admin.register(ProjectAttachment)
class ProjectAttachmentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'project', 'file_size', 'uploaded_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('file_name', 'description', 'project__title')
    readonly_fields = ('id', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    raw_id_fields = ('project', 'uploaded_by')
    
    fieldsets = (
        (None, {
            'fields': ('id', 'project', 'file', 'file_name')
        }),
        ('Details', {
            'fields': ('file_size', 'description', 'uploaded_by')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )