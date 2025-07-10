from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .models import LoanApplication
from django.core import mail

class LoanTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user   = User.objects.create_user("tester","t@x.com","pass")
        self.client.force_authenticate(user=self.user)

    def test_successful_application(self):
        res = self.client.post("/api/loan/apply/", {
            "amount_requested": "100000",
            "purpose": "Rent"
        })
        self.assertEqual(res.status_code, 201)
        self.assertTrue(res.data["success"])
        self.assertEqual(res.data["data"]["status"], "pending")

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_fraud_multiple_loans_sends_email(self):
        # Seed 3 loans
        for _ in range(3):
            LoanApplication.objects.create(user=self.user, amount_requested=50000, purpose="x")
        mail.outbox = []
        res = self.client.post("/api/loan/apply/", {
            "amount_requested": "100000",
            "purpose": "Urgent"
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data["data"]["status"], "flagged")
        # One email should be sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Loan #", mail.outbox[0].subject)
