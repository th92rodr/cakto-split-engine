from django.urls import path

from app.api.views import ConfirmPaymentView, CheckoutQuoteView

urlpatterns = [
    path("payments", ConfirmPaymentView.as_view()),
    path("checkout/quote", CheckoutQuoteView.as_view()),
]
