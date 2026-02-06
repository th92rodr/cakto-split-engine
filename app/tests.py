from decimal import Decimal

from app.models import Payment, OutboxEvent
from app.services import PaymentService, SplitInput

def test_pix_zero_fee_single_split(db):
    result = PaymentService.confirm_payment(
        idempotency_key="test_pix_1",
        amount=Decimal("100.00"),
        currency="BRL",
        payment_method=Payment.PaymentMethod.PIX,
        installments=1,
        splits=[
            SplitInput(recipient_id="producer_1", role="producer", percent=100),
        ],
    )

    assert result.status == Payment.Status.CAPTURED
    assert result.gross_amount == Decimal("100.00")
    assert result.platform_fee_amount == Decimal("0.00")
    assert result.net_amount == Decimal("100.00")

    assert len(result.receivables) == 1
    assert result.receivables[0].recipient_id == "producer_1"
    assert result.receivables[0].role == "producer"
    assert result.receivables[0].amount == Decimal("100.00")

    assert result.outbox_event.type == "payment_captured"
    assert result.outbox_event.status == OutboxEvent.Status.PENDING
