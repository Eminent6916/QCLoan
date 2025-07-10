from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework import generics, permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView

from .models import LoanApplication, FraudFlag
# from rest_framework_simplejwt.authentication.JWTAuthentication import authenticate
# from rest_framework_simplejwt.tokens import Token

from .permission import IsAdminUser
from .serializers import UserRegisterSerializer, LoanApplicationSerializer, \
    LoginSerializer, FlaggedLoanSerializer, LoanUpdateSerializer
from .utils import error_response, success_response, require_fields, handle_exception, detect_fraud, \
    notify_admin_of_flagged, generate_login_response


class HomeAPIView(APIView):
    def get(self, request):
        return success_response('Welcome to QuickCheck Loan API')

class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer

class LoginAPIView(GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]

            user = authenticate(username=username, password=password)
            if not user:
                return error_response("Invalid credentials", code=status.HTTP_401_UNAUTHORIZED)

            # token, _ = Token.objects.get_or_create(user=user)
            return success_response("Login successful", generate_login_response(user))

        except Exception as exc:
            return handle_exception(exc)


class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            request.user.auth_token.delete()
            return success_response("User Logged out successful")
        except Exception as e:
            return error_response("Logout failed", str(e), code=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SubmitLoanAPIView(GenericAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    queryset = LoanApplication.objects.all()
    serializer_class = LoanApplicationSerializer

    def post(self, request):
        try:
            require_fields(request.data, ['amount_requested','purpose'])
            amount = float(request.data['amount_requested'])
            reasons = detect_fraud(request.user, amount)
            status_str = LoanApplication.FLAGGED if reasons else LoanApplication.PENDING

            loan = LoanApplication.objects.create(
                user=request.user,
                amount_requested=amount,
                purpose=request.data['purpose'],
                status=status_str
            )
            # for r in reasons:
            #     FraudFlag.objects.create(loan_application=loan, reason=r)

            if reasons:
                # message = " ".join(f"{i + 1}. {r}" for i, r in enumerate(reasons))
                message =" ".join(f" - {r}" for r in reasons)
                FraudFlag.objects.create(loan_application=loan, reason=message)

                notify_admin_of_flagged(loan, reasons)

            data = LoanApplicationSerializer(loan).data
            return success_response("Loan submitted", data, code=status.HTTP_201_CREATED)
        except Exception as exc:
            return handle_exception(exc)

# — List own loans — #
class MyLoansAPIView(generics.ListAPIView):
    serializer_class = LoanApplicationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return LoanApplication.objects.filter(user=self.request.user)

# — Admin actions — #
class AdminLoanActionAPIView(GenericAPIView):
    permission_classes = (permissions.IsAuthenticated, IsAdminUser)
    serializer_class = LoanUpdateSerializer

    def post(self, request, pk, action):
        serializer = self.get_serializer(data=request.data)

        try:
            loan = LoanApplication.objects.get(pk=pk)
            if action not in ['approve','reject','flag']:
                return error_response("Invalid action", code=status.HTTP_400_BAD_REQUEST)

            if action == 'approve':
                loan.status = LoanApplication.APPROVED
            elif action == 'reject':
                loan.status = LoanApplication.REJECTED
            else:
                loan.status = LoanApplication.FLAGGED
                FraudFlag.objects.create(loan_application=loan, reason='Manually flagged')
                notify_admin_of_flagged(loan, ['Manually flagged'])

            loan.save()
            return success_response(f"Loan {action}d", {'status': loan.status})
        except Exception as exc:
            return handle_exception(exc)

class FetchLoansByStatusAPIView(generics.ListAPIView):
    serializer_class = LoanApplicationSerializer
    permission_classes = (permissions.IsAuthenticated, IsAdminUser)

    def get_queryset(self):
        valid_status = ['pending', 'approved', 'rejected', 'flagged']
        status = self.request.query_params.get('status', '').lower()
        if status in valid_status:
            # return LoanApplication.objects.all()
            return LoanApplication.objects.filter(status=status).select_related('user')

            # No status provided or invalid -> fetch all
        return LoanApplication.objects.all().select_related('user')

class FlaggedLoanListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = FlaggedLoanSerializer
    queryset = FraudFlag.objects.select_related('loan_application__user').all()

