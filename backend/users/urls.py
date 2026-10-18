from django.urls import path

from .views import login_view, logout_view, register, verify_otp

app_name = "users"

urlpatterns = [
    path("register/", register, name="register"),
    path("verify-otp/", verify_otp, name="verify_otp"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
]