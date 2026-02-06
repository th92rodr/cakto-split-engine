from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass

from app.models import Payment

@dataclass(frozen=True)
class CalculationResult:
    gross_amount: Decimal
    platform_fee_amount: Decimal
    net_amount: Decimal


class CalculationService:
    @staticmethod
    def calculate(*, amount: Decimal, payment_method: str, installments: int) -> CalculationResult:
        fee_rate = CalculationService._get_fee_rate(payment_method=payment_method, installments=installments)

        platform_fee = (amount * fee_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        net_amount = (amount - platform_fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return CalculationResult(
            gross_amount=amount,
            platform_fee_amount=platform_fee,
            net_amount=net_amount,
        )

    @staticmethod
    def _get_fee_rate(*, payment_method: str, installments: int) -> Decimal:
        method = payment_method.lower()

        if method == Payment.PaymentMethod.PIX:
            if installments != 1:
                raise InvalidInstallments("PIX does not support installments")
            return Decimal("0.00")

        if method == Payment.PaymentMethod.CARD:
            if installments < 1 or installments > 12:
                raise InvalidInstallments("CARD installments must be between 1 and 12")

            if installments == 1:
                return Decimal("0.0399")

            extra_installments = installments - 1
            return Decimal("0.0499") + (Decimal("0.02") * extra_installments)

        raise UnsupportedPaymentMethod(f"Unsupported payment method: {payment_method}")


class UnsupportedPaymentMethod(Exception):
    pass

class InvalidInstallments(Exception):
    pass
