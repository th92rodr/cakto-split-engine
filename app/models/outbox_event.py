from django.db import models

from app.models import Payment

class OutboxEvent(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PUBLISHED = "published", "Published"

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="outbox_events",
        db_column="payment_id",
    )

    type = models.CharField(
        max_length=50,
        help_text="Event type (e.g. payment_captured)",
    )

    payload = models.JSONField(
        help_text="Event payload",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "outbox_events"
        indexes = [
            models.Index(fields=["payment"]),
            models.Index(fields=["type"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"OutboxEvent {self.id} - {self.type} - {self.status}"
