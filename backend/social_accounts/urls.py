from django.urls import path
from .views import GoogleOauthSignInview


urlpatterns=[
    path('google/', GoogleOauthSignInview.as_view(), name='google')
]