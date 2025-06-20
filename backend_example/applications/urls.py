from django.urls import path
from .views import (
    ApplicationListCreateView,
    ApplicationDetailView,
    ApplicationStatusUpdateView,
    WithdrawApplicationView,
    UserApplicationsView,
    ProjectApplicationsView
)

urlpatterns = [
    # List applications and create a new application
    path('', ApplicationListCreateView.as_view(), name='application-list-create'),
    
    # Application detail, update and deletion
    path('<uuid:pk>/', ApplicationDetailView.as_view(), name='application-detail'),
    
    # Update application status (accept/reject)
    path('<uuid:pk>/status/', ApplicationStatusUpdateView.as_view(), name='application-status-update'),
    
    # Withdraw an application
    path('<uuid:pk>/withdraw/', WithdrawApplicationView.as_view(), name='application-withdraw'),
    
    # Current user's applications
    path('user/', UserApplicationsView.as_view(), name='user-applications'),
    
    # Applications for a specific project
    path('project/<uuid:project_id>/', ProjectApplicationsView.as_view(), name='project-applications'),
]