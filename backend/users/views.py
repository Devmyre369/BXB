
import random
from datetime import timedelta

from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import RegistrationForm
from .models import EmailOTP, User
from .utils import send_otp_email


def register(request):
    if request.user.is_authenticated:
        return redirect("feed")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            # Generate a six-digit OTP.
            otp = str(random.randint(100000, 999999))

            # Store registration information temporarily.
            request.session["registration_data"] = {
                "username": username,
                "email": email,
                "password": password,
            }

            # Create OTP with a 10-minute expiry.
            EmailOTP.objects.create(
                email=email,
                otp=otp,
                expires_at=timezone.now() + timedelta(minutes=10),
            )

            send_otp_email(email, otp)

            return redirect("verify_otp")

    else:
        form = RegistrationForm()

    return render(
        request,
        "users/register.html",
        {"form": form},
    )


def verify_otp(request):
    if request.user.is_authenticated:
        return redirect("feed")

    registration_data = request.session.get("registration_data")

    if not registration_data:
        return redirect("register")

    email = registration_data["email"]

    otp_record = (
        EmailOTP.objects.filter(
            email=email,
            verified=False,
        )
        .order_by("-created_at")
        .first()
    )

    if not otp_record:
        return redirect("register")

    error = None

    if request.method == "POST":
        submitted_otp = request.POST.get("otp", "").strip()

        if otp_record.attempts >= 5:
            error = "Maximum OTP attempts exceeded. Please register again."

        elif otp_record.expires_at < timezone.now():
            error = "Your OTP has expired. Please register again."

        elif submitted_otp != otp_record.otp:
            otp_record.attempts += 1
            otp_record.save(update_fields=["attempts"])
            error = "Invalid OTP. Please try again."

        else:
            try:
                with transaction.atomic():
                    otp_record.verified = True
                    otp_record.save(update_fields=["verified"])

                    user = User.objects.create_user(
                        username=registration_data["username"],
                        email=registration_data["email"],
                        password=registration_data["password"],
                    )

                request.session.pop("registration_data", None)

                login(request, user)

                return redirect("feed")

            except IntegrityError:
                error = (
                    "An account with this username or email already exists. "
                    "Please register again."
                )

    return render(
        request,
        "users/verify_otp.html",
        {
            "email": email,
            "error": error,
        },
    )


def login_view(request):
    next_url = request.POST.get("next") or request.GET.get("next", "")

    if request.user.is_authenticated:
        if next_url and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)

        return redirect("feed")

    if request.method == "POST":
        form = AuthenticationForm(
            request,
            data=request.POST,
        )

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            return redirect("feed")

    else:
        form = AuthenticationForm(request)

    return render(
        request,
        "users/login.html",
        {
            "form": form,
            "next": next_url,
        },
    )


def logout_view(request):
    logout(request)
    return redirect("home")
