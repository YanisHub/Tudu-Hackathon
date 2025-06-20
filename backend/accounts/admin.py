from django.contrib import admin
from .models import (
    User, 
    OneTimePassword,
    UserProfile,
    UserExpertise,
    ExpertiseArea
)
# Register your models here.

admin.site.register(User)
admin.site.register(OneTimePassword)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')
    search_fields = ('user__email',)
    list_filter = ('created_at',)


@admin.register(ExpertiseArea)
class ExpertiseAreaAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)


@admin.register(UserExpertise)
class UserExpertiseAdmin(admin.ModelAdmin):
    list_display = ('user', 'expertise', 'is_verified')
    search_fields = ('user__email', 'expertise__name')
    list_filter = ('proficiency_level', 'is_verified', 'created_at')