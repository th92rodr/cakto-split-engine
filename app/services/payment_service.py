import json
import hashlib
from django.db import transaction
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Any

from app.models import Payment, LedgerEntry, OutboxEvent
from app.services import CalculationService, SplitService, SplitInput

@dataclass(frozen=True)
class ReceivableDTO:
    recipient_id: str
    role: str
    amount: Decimal

@dataclass(frozen=True)
class OutboxEventDTO:
    type: str
    status: str

@dataclass(frozen=True)
class PaymentResultDTO:
    payment_id: str
    status: str
    gross_amount: Decimal
    platform_fee_amount: Decimal
    net_amount: Decimal
    receivables: List[ReceivableDTO]
    outbox_event: OutboxEventDTO


class PaymentService:
    @staticmethod
    @transaction.atomic
    def confirm_payment(*, idempotency_key: str, amount: Decimal, currency: str, payment_method: str, installments: int, splits: list[SplitInput]) -> PaymentResultDTO:
        payload = {
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "installments": installments,
            "splits": [
                {
                    "recipient_id": split.recipient_id,
                    "role": split.role,
                    "percent": split.percent,
                }
                for split in splits
            ],
        }
        payload_hash = PaymentService._generate_payload_hash(payload)

        existing = Payment.objects.filter(
            idempotency_key=idempotency_key
        ).first()

        if existing:
            if existing.payload_hash != payload_hash:
                raise IdempotencyConflict("Idempotency-Key reused with different payload")

            ledger_entries = LedgerEntry.objects.filter(payment_id=existing.id)
            outbox_event = (
                existing.outbox_events
                .order_by("-created_at")
                .first()
            )

            return PaymentResultDTO(
                payment_id=str(existing.id),
                status=existing.status,
                gross_amount=existing.gross_amount,
                platform_fee_amount=existing.platform_fee_amount,
                net_amount=existing.net_amount,
                receivables=[
                    ReceivableDTO(
                        recipient_id=ledger_entry.recipient_id,
                        role=ledger_entry.role,
                        amount=ledger_entry.amount,
                    ) for ledger_entry in ledger_entries
                ],
                outbox_event=OutboxEventDTO(
                    type=outbox_event.type,
                    status=outbox_event.status,
                ),
            )

        calculation = CalculationService.calculate(
            amount=amount,
            payment_method=payment_method,
            installments=installments,
        )

        split_results = SplitService.calculate(
            net_amount=calculation.net_amount,
            splits=splits,
        )

        payment = Payment.objects.create(
            status=Payment.Status.CAPTURED,
            payment_method=payment_method,
            idempotency_key=idempotency_key,
            gross_amount=calculation.gross_amount,
            platform_fee_amount=calculation.platform_fee_amount,
            net_amount=calculation.net_amount,
            installments=installments,
            payload_hash=payload_hash,
            currency=currency,
        )

        ledger_entries = LedgerEntry.objects.bulk_create(
            [
                LedgerEntry(
                    payment_id=payment.id,
                    recipient_id=split.recipient_id,
                    role=split.role,
                    amount=split.amount,
                )
                for split in split_results
            ]
        )

        outboxEvent = OutboxEvent.objects.create(
            payment_id=payment.id,
            type="payment_captured",
            status=OutboxEvent.Status.PENDING,
            payload={
                "payment_id": str(payment.id),
                "gross_amount": str(calculation.gross_amount),
                "net_amount": str(calculation.net_amount),
                "receivables": [
                    {
                        "recipient_id": split.recipient_id,
                        "role": split.role,
                        "amount": str(split.amount),
                    }
                    for split in split_results
                ],
            },
        )

        return PaymentResultDTO(
            payment_id=str(payment.id),
            status=payment.status,
            gross_amount=payment.gross_amount,
            platform_fee_amount=payment.platform_fee_amount,
            net_amount=payment.net_amount,
            receivables=[
                ReceivableDTO(
                    recipient_id=ledger_entry.recipient_id,
                    role=ledger_entry.role,
                    amount=ledger_entry.amount,
                ) for ledger_entry in ledger_entries
            ],
            outbox_event=OutboxEventDTO(
                type=outboxEvent.type,
                status=outboxEvent.status,
            ),
        )

    @staticmethod
    def _generate_payload_hash(payload: dict) -> str:
        normalized = PaymentService._normalize(payload)

        raw = json.dumps(
            normalized,
            separators=(",", ":"),
            sort_keys=True,
        )

        return hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def _normalize(obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, list):
            return [PaymentService._normalize(i) for i in obj]
        if isinstance(obj, dict):
            return {k: PaymentService._normalize(obj[k]) for k in sorted(obj)}
        return obj


class IdempotencyConflict(Exception):
    pass
