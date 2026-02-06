from decimal import Decimal
from rest_framework import serializers

class SplitSerializer(serializers.Serializer):
    recipient_id = serializers.CharField()
    role = serializers.CharField()
    percent = serializers.IntegerField(min_value=1, max_value=100)

class PaymentInputSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    payment_method = serializers.CharField()
    installments = serializers.IntegerField()
    splits = SplitSerializer(many=True)

    def validate_amount(self, value: Decimal):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError("Amount must be greater than zero")
        return value

    def validate_currency(self, value: str):
        value = value.upper()
        if value != "BRL":
            raise serializers.ValidationError("Only BRL is supported")
        return value

    def validate_payment_method(self, value: str):
        value = value.lower()
        if value not in ("pix", "card"):
            raise serializers.ValidationError("Unsupported payment method")
        return value

    def validate(self, data):
        splits = data.get("splits", [])

        if not (1 <= len(splits) <= 5):
            raise serializers.ValidationError("Splits must contain between 1 and 5 recipients")

        total_percent = sum(split["percent"] for split in splits)
        if total_percent != 100:
            raise serializers.ValidationError("Split percentages must sum to 100")

        payment_method = data["payment_method"]
        installments = data["installments"]

        if payment_method == "pix" and installments != 1:
            raise serializers.ValidationError("PIX does not support installments")

        if payment_method == "card" and not (1 <= installments <= 12):
            raise serializers.ValidationError("Card installments must be between 1 and 12")

        return data
