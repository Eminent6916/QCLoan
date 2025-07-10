from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class LoanApplication(models.Model):
    PENDING   = 'pending'
    APPROVED  = 'approved'
    REJECTED  = 'rejected'
    FLAGGED   = 'flagged'
    STATUS_CHOICES = [
        (PENDING,   'Pending'),
        (APPROVED,  'Approved'),
        (REJECTED,  'Rejected'),
        (FLAGGED,   'Flagged'),
    ]

    user             = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    amount_requested = models.DecimalField(max_digits=12, decimal_places=2)
    purpose          = models.TextField()
    status           = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    date_applied     = models.DateTimeField(auto_now_add=True)
    date_updated     = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}: {self.amount_requested} ({self.status})"

class FraudFlag(models.Model):
    loan_application = models.ForeignKey(LoanApplication, on_delete=models.CASCADE, related_name='fraud_flags')
    reason           = models.CharField(max_length=255)
    date_flagged     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Loan#{self.loan_application.id} flagged: {self.reason}"


