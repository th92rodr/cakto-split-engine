from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from app.api.serializers import PaymentInputSerializer
from app.api.exceptions import translate_exception
from app.services import PaymentService, CalculationService, SplitInput

class ConfirmPaymentView(APIView):
    def post(self, request):
        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return Response({
                "detail": "Idempotency-Key header is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PaymentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        splits: list[SplitInput] = []
        for split in data["splits"]:
            splits.append(SplitInput(
                recipient_id=split["recipient_id"],
                role=split["role"],
                percent=split["percent"],
            ))

        try:
            result = PaymentService.confirm_payment(
                idempotency_key=idempotency_key,
                amount=data["amount"],
                currency=data["currency"],
                payment_method=data["payment_method"],
                installments=data["installments"],
                splits=splits,
            )
        except Exception as exception:
            translate_exception(exception)

        return Response(
            {
                "payment_id": result.payment_id,
                "status": result.status,
                "gross_amount": float(result.gross_amount),
                "platform_fee_amount": float(result.platform_fee_amount),
                "net_amount": float(result.net_amount),
                "receivables": [
                    {
                        "recipient_id": r.recipient_id,
                        "role": r.role,
                        "amount": float(r.amount),
                    }
                    for r in result.receivables
                ],
                "outbox_event": {
                    "type": result.outbox_event.type,
                    "status": result.outbox_event.status,
                },
            },
            status=status.HTTP_201_CREATED,
        )

class CheckoutQuoteView(APIView):
    def post(self, request):
        serializer = PaymentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = CalculationService.calculate(
                amount=data["amount"],
                payment_method=data["payment_method"],
                installments=data["installments"],
            )
        except Exception as exception:
            translate_exception(exception)

        return Response(
            {
                "gross_amount": float(result.gross_amount),
                "platform_fee_amount": float(result.platform_fee_amount),
                "net_amount": float(result.net_amount),
            },
            status=status.HTTP_200_OK,
        )
