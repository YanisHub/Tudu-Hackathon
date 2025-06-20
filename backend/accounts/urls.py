from django.urls import path
from .views import (
    RegisterView,
    VerifyUserEmail,
    LoginUserView,
    TestingAuthenticatedReq,
    PasswordResetConfirm,
    PasswordResetRequestView,
    SetNewPasswordView,
    LogoutApiView,
    UserProfileView,
    ExpertiseAreaListView,
    ExpertiseAreaCreateView,
    ExpertiseAreaDetailView,
    UserExpertiseListView,
    UserExpertiseDetailView,
    AvailableExpertiseView,
    CurrentUserView
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Auth endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyUserEmail.as_view(), name='verify'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', LoginUserView.as_view(), name='login-user'),
    path('logout/', LogoutApiView.as_view(), name='logout'),
    
    # Password reset endpoints
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirm.as_view(), name='reset-password-confirm'),
    path('set-new-password/', SetNewPasswordView.as_view(), name='set-new-password'),
    
    # Test endpoint
    path('get-something/', TestingAuthenticatedReq.as_view(), name='just-for-testing'),
    
    # User profile endpoints
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('current-user/', CurrentUserView.as_view(), name='current-user'),
    
    # Expertise area endpoints
    path('expertise-areas/', ExpertiseAreaListView.as_view(), name='expertise-areas-list'),
    path('expertise-areas/create/', ExpertiseAreaCreateView.as_view(), name='expertise-areas-create'),
    path('expertise-areas/<uuid:pk>/', ExpertiseAreaDetailView.as_view(), name='expertise-areas-detail'),
    
    # User expertise endpoints
    path('user-expertise/', UserExpertiseListView.as_view(), name='user-expertise-list'),
    path('user-expertise/<uuid:pk>/', UserExpertiseDetailView.as_view(), name='user-expertise-detail'),
    path('available-expertise/', AvailableExpertiseView.as_view(), name='available-expertise'),
]