from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .models import LoanApplication
from django.core import mail


class LoanApplicationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            first_name="Tester",
            last_name="Test",
            username="tester",
            email="t@x.com",
            password="pass"
        )
        self.authenticate()


    def authenticate(self):
        return self.client.force_authenticate(user=self.user)

    def create_loan(self, amount=100000, purpose="Test"):
        return self.client.post("/api/loan/apply/", {
            "amount_requested": amount,
            "purpose": purpose
        })

    def test_successful_application(self):
        response = self.create_loan(purpose="Rent")

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response)
        self.assertEqual(response.data["data"]["status"], "pending")

        loan = LoanApplication.objects.first()
        self.assertEqual(loan.amount_requested, 100000)
        self.assertEqual(loan.status, "pending")
        self.assertEqual(LoanApplication.objects.count(), 1)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_fraud_multiple_loans_sends_email(self):
        # Simulate 3 previous loans
        for _ in range(3):
            LoanApplication.objects.create(
                user=self.user,
                amount_requested=50000,
                purpose="Test"
            )

        mail.outbox = []
        response = self.create_loan(amount=100000, purpose="Urgent")

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["status"], "flagged")

        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Loan", mail.outbox[0].subject)
        self.assertIn("Too many applications", mail.outbox[0].body)
