from django.urls import path
from .views import *

urlpatterns = [
    path("test/", test_api),
    path("create/", create_user),
    path("login/", verify_user),
    path("refresh/", refresh_token),
    path("verify-admin/", verify_user_admin),
    path("logout/", logout_user),
]