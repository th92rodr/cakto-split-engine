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

def test_card_3x_split_70_30(db):
    result = PaymentService.confirm_payment(
        idempotency_key="test_card_3x",
        amount=Decimal("100.00"),
        currency="BRL",
        payment_method=Payment.PaymentMethod.CARD,
        installments=3,
        splits=[
            SplitInput(recipient_id="producer_1", role="producer", percent=70),
            SplitInput(recipient_id="affiliate_1", role="affiliate", percent=30),
        ],
    )

    assert result.status == Payment.Status.CAPTURED
    assert result.gross_amount == Decimal("100.00")
    assert result.platform_fee_amount == Decimal("8.99")
    assert result.net_amount == Decimal("91.01")

    assert len(result.receivables) == 2
    assert result.receivables[0].recipient_id == "producer_1"
    assert result.receivables[0].role == "producer"
    assert result.receivables[0].amount == Decimal("63.71")
    assert result.receivables[1].recipient_id == "affiliate_1"
    assert result.receivables[1].role == "affiliate"
    assert result.receivables[1].amount == Decimal("27.30")

    total = sum(r.amount for r in result.receivables)
    assert total == result.net_amount

    assert result.outbox_event.type == "payment_captured"
    assert result.outbox_event.status == OutboxEvent.Status.PENDING

def test_rounding_remainder_goes_to_highest_percent(db):
    result = PaymentService.confirm_payment(
        idempotency_key="test_remainder",
        amount=Decimal("10.01"),
        currency="BRL",
        payment_method=Payment.PaymentMethod.PIX,
        installments=1,
        splits=[
            SplitInput(recipient_id="producer_1", role="producer", percent=70),
            SplitInput(recipient_id="affiliate_1", role="affiliate", percent=30),
        ],
    )

    assert result.status == Payment.Status.CAPTURED
    assert result.gross_amount == Decimal("10.01")
    assert result.platform_fee_amount == Decimal("0.00")
    assert result.net_amount == Decimal("10.01")

    assert len(result.receivables) == 2
    assert result.receivables[0].recipient_id == "producer_1"
    assert result.receivables[0].role == "producer"
    assert result.receivables[0].amount == Decimal("7.01")
    assert result.receivables[1].recipient_id == "affiliate_1"
    assert result.receivables[1].role == "affiliate"
    assert result.receivables[1].amount == Decimal("3.00")

    total = sum(r.amount for r in result.receivables)
    assert total == result.net_amount

    assert result.outbox_event.type == "payment_captured"
    assert result.outbox_event.status == OutboxEvent.Status.PENDING

def test_idempotency_same_key_same_payload_returns_same_payment(db):
    args = dict(
        idempotency_key="test_idempotency",
        amount=Decimal("100.00"),
        currency="BRL",
        payment_method=Payment.PaymentMethod.PIX,
        installments=1,
        splits=[SplitInput(recipient_id="producer_1", role="producer", percent=100)],
    )

    result1 = PaymentService.confirm_payment(**args)
    result2 = PaymentService.confirm_payment(**args)

    assert result1.payment_id == result2.payment_id
