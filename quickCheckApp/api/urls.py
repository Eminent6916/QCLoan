from django.urls import path
from . import views
from .views import RegisterAPIView, LoginAPIView, MyLoansAPIView, SubmitLoanAPIView, AdminLoanActionAPIView, \
     FlaggedLoanListAPIView, FetchLoansByStatusAPIView

urlpatterns = [
    path("", views.HomeAPIView.as_view(), name="home"),
    path("register/", RegisterAPIView.as_view(), name="register"),
    path("login", LoginAPIView.as_view(), name="login"),
    path("logout/", views.LogoutAPIView.as_view(), name="logout"),
    path("loan/apply/", SubmitLoanAPIView.as_view(), name="Apply-loan"),
    path("loan/", MyLoansAPIView.as_view(), name="my-loans"),
    path("loan/<int:pk>/<str:action>/", AdminLoanActionAPIView.as_view(), name="admin-action-on-loan"),
    path("loan/status/", FetchLoansByStatusAPIView.as_view(), name="fetch-by-loan-status"),
    # path("lo")
    path("flagged-loan/", FlaggedLoanListAPIView.as_view(), name="flagged-loan")
]
