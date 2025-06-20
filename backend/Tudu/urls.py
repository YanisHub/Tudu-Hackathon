
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include



urlpatterns = [
    
    # ---- API Auth : test API browser ---- #
    path('api-auth/', include('rest_framework.urls')),
    
    
    # ---- ADMIN ---- #
    path('api/admin/', admin.site.urls),
    
    
    # ---- Authentication ---- #
    path('api/auth/', include("accounts.urls")),
    path('api/auth/', include('social_accounts.urls')),
    
    # ---- Projects Management ---- #
    path('api/projects/', include("projects.urls")),
    
    # ---- Applications Management ---- #
    path('api/applications/', include("applications.urls")),
    
    # ---- Chat Management ---- #
    path('api/chat/', include("chat.urls")),
    
    # ---- Payments Management ---- #
    path('api/payments/', include("payments.urls")),
    
    # ---- Notifications Management ---- #
    path('api/notifications/', include("notifications.urls"))
    
    
] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
