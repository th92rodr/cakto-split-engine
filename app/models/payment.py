from django.db import models

class Payment(models.Model):
    class Status(models.TextChoices):
        CAPTURED = "captured", "Captured"

    class PaymentMethod(models.TextChoices):
        PIX = "pix", "PIX"
        CARD = "card", "Card"

    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        help_text="Key used to guarantee idempotent payment creation",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CAPTURED,
    )

    gross_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Original payment amount",
    )

    platform_fee_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Fee charged by the platform",
    )

    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount after platform fees",
    )

    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
    )

    installments = models.PositiveSmallIntegerField(
        help_text="Number of installments",
    )

    currency = models.CharField(max_length=3)

    payload_hash = models.CharField(max_length=64)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments"
        indexes = [
            models.Index(fields=["idempotency_key"]),
        ]

    def __str__(self):
        return f"Payment {self.id} - {self.payment_method} - {self.status}"
