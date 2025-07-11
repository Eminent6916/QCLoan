from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
# from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from api.models import LoanApplication

# from .loan.models import LoanApplication

# from .models import LoanApplication

# —— Standardized API Responses —— #
def success_response(message="Success", data=None, code=status.HTTP_200_OK):
    return Response({"success": True, "message": message, "data": data}, status=code)

def error_response(message="Error", errors=None, code=status.HTTP_400_BAD_REQUEST):
    return Response({"success": False, "message": message, "errors": errors}, status=code)

def handle_exception(exc):
    if isinstance(exc, ValidationError):
        return error_response("Validation failed", errors=exc.detail, code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    if isinstance(exc, ObjectDoesNotExist):
        return error_response("Not found", code=status.HTTP_404_NOT_FOUND)
    return error_response("Server error", errors=str(exc), code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# —— Request-data Validation —— #
def require_fields(data, fields):
    missing = [f for f in fields if not data.get(f)]
    if missing:
        raise ValidationError({f: "This field is required." for f in missing})

# —— Fraud-Detection Logic —— #
def detect_fraud(user, amount):
    reasons = []
    now = timezone.now()
    # 1) >3 loans in past 24h
    count_24h = LoanApplication.objects.filter(
        user=user,
        date_applied__gte=now - timedelta(hours=24)
    ).count()
    if count_24h >= 3:
        reasons.append("Too many applications in 24h")

    # 2) Large amount
    if amount > 5_000_000:
        reasons.append("Amount exceeds NGN 5,000,000")

    # 3) Shared email-domain clusters
    domain = user.email.split("@")[-1]
    if User.objects.filter(email__iendswith=domain).count() > 10:
        reasons.append("Email domain used by >10 users")

    return reasons

def notify_admin_of_flagged(loan, reasons):
    subject = f"Loan #{loan.id} flagged for review"
    message = (
        f"User: {loan.user.username}\n"
        f"Amount: {loan.amount_requested}\n"
        "Reasons:\n" + "\n".join(f"- {r}" for r in reasons)
    )
    send_mail(subject, message, None, ['admin@quickcheck.com'])

def generate_login_response(user):
    token, _ = Token.objects.get_or_create(user=user)
    return {
        "token": token.key,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "fullname": user.get_full_name()
        }
    }
