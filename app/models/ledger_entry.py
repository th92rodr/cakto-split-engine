from django.db import models

from app.models import Payment

class LedgerEntry(models.Model):
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="ledger_entries",
        db_column="payment_id",
    )

    recipient_id = models.CharField(
        max_length=255,
        help_text="Identifier of the payment recipient",
    )

    role = models.CharField(
        max_length=50,
        help_text="Role of the recipient (producer, affiliate, etc)",
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount assigned to this recipient",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ledger_entries"
        indexes = [
            models.Index(fields=["payment"]),
            models.Index(fields=["recipient_id"]),
        ]

    def __str__(self):
        return f"LedgerEntry {self.id} - {self.role} - {self.recipient_id}"
