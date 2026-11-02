
import random
from datetime import timedelta

from django.conf import settings
from django.core.mail import get_connection, send_mail
from django.utils import timezone

from .models import EmailOTP


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email):
    otp = generate_otp()

    expires_at = timezone.now() + timedelta(minutes=5)

    # Remove previous unverified OTPs.
    EmailOTP.objects.filter(
        email=email,
        verified=False
    ).delete()

    # Save the new OTP.
    EmailOTP.objects.create(
        email=email,
        otp=otp,
        expires_at=expires_at
    )

    print("\n===== BXB SMTP DIAGNOSTICS =====")
    print("Backend:", settings.EMAIL_BACKEND)
    print("Host:", settings.EMAIL_HOST)
    print("Port:", settings.EMAIL_PORT)
    print("TLS:", settings.EMAIL_USE_TLS)
    print("SSL:", settings.EMAIL_USE_SSL)
    print("Username configured:", bool(settings.EMAIL_HOST_USER))
    print("Password configured:", bool(settings.EMAIL_HOST_PASSWORD))
    print("Password length:", len(settings.EMAIL_HOST_PASSWORD or ""))

    try:
        email_connection = get_connection()

        print(
            "Connection class:",
            type(email_connection).__name__
        )

        result = send_mail(
            subject="Your BxB Email Verification OTP",
            message=(
                f"Your BitsXBytes verification OTP is: {otp}\n\n"
                "This OTP is valid for 5 minutes.\n"
                "Do not share this OTP with anyone."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
            connection=email_connection,
        )

        print("Email send result:", result)
        print("===== BXB EMAIL SENT SUCCESSFULLY =====")

        return result

    except Exception as error:
        print("\n===== BXB SMTP FAILURE =====")
        print("Exception:", type(error).__name__)
        print("Details:", str(error))
        raise
