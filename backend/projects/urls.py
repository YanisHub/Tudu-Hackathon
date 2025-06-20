# In your projects/urls.py

from django.urls import path
from . import views

# Define app_name if you need namespacing (optional but recommended)
app_name = 'projects'

urlpatterns = [
    # List views specific to the user
    path('owner/', views.MyOwnedProjectsListView.as_view(), name='owner-projects'),
    path('collaborator/', views.MyCollaboratingProjectsListView.as_view(), name='collaborator-projects'),
    path('applications/', views.MyAppliedProjectsListView.as_view(), name='applied-projects'),

    # Marketplace view
    path('discover/', views.ProjectMarketplaceListView.as_view(), name='project-discover'),

    # Project CRUD
    path('new/', views.ProjectCreateView.as_view(), name='project-new'),
    path('<uuid:pk>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path('<uuid:pk>/edit/', views.ProjectModifyView.as_view(), name='project-edit'), # Includes GET(retrieve), PUT, PATCH, DELETE

    # Project Attachements (nested under a specific project)
    path('<uuid:project_pk>/files/', views.ProjectAttachmentListCreateView.as_view(), name='project-files'),
    path('<uuid:project_pk>/files/<uuid:attachment_pk>/', views.ProjectAttachmentDetailView.as_view(), name='project-file-detail'),
]

