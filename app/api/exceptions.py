from rest_framework import status
from rest_framework.exceptions import APIException

from app.services import (
    IdempotencyConflict,
    UnsupportedPaymentMethod,
    InvalidInstallments,
    EmptySplitError,
    InvalidSplitPercentage,
)

class ConflictError(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict"
    default_code = "conflict"

class BadRequestError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Bad request"
    default_code = "bad_request"

EXCEPTION_MAPPING = {
    IdempotencyConflict: ConflictError,
    UnsupportedPaymentMethod: BadRequestError,
    InvalidInstallments: BadRequestError,
    EmptySplitError: BadRequestError,
    InvalidSplitPercentage: BadRequestError,
}

def translate_exception(exception: Exception):
    for exception_type, api_exception in EXCEPTION_MAPPING.items():
        if isinstance(exception, exception_type):
            raise api_exception(str(exception))
    raise exception
