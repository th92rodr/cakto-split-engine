from decimal import Decimal, ROUND_DOWN
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class SplitInput:
    recipient_id: str
    role: str
    percent: int

@dataclass(frozen=True)
class SplitResult:
    recipient_id: str
    role: str
    percent: int
    amount: Decimal


class SplitService:
    @staticmethod
    def calculate(*, net_amount: Decimal, splits: List[SplitInput]) -> List[SplitResult]:
        if not splits:
            raise EmptySplitError("At least one split is required")

        for split in splits:
            if split.percent <= 0 or split.percent > 100:
                raise InvalidSplitPercentage(f"Invalid split percent: {split.percent}")

        total_percent = sum(s.percent for s in splits)
        if total_percent != 100:
            raise InvalidSplitPercentage("Split percentages must sum to 100")

        results: List[SplitResult] = []
        total_distributed = Decimal("0.00")

        for split in splits:
            raw = (net_amount * Decimal(split.percent) / Decimal("100"))
            amount = raw.quantize(Decimal("0.01"), rounding=ROUND_DOWN)

            results.append(SplitResult(
                recipient_id=split.recipient_id,
                role=split.role,
                percent=split.percent,
                amount=amount,
            ))
            total_distributed += amount

        remainder = (net_amount - total_distributed).quantize(Decimal("0.01"))

        if remainder > Decimal("0.00"):
            target = max(results, key=lambda r: r.percent)
            results = [
                SplitResult(
                    recipient_id=r.recipient_id,
                    role=r.role,
                    percent=r.percent,
                    amount=r.amount + remainder if r is target else r.amount,
                )
                for r in results
            ]

        return results


class SplitError(Exception):
    pass

class EmptySplitError(SplitError):
    pass

class InvalidSplitPercentage(SplitError):
    pass
