from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from stock import services


def handle_stock_errors(exc, context):
    """DRF exception handler: maps warehouse errors to HTTP responses."""
    if isinstance(exc, services.InsufficientStock):
        return Response(
            {
                'detail': 'Not enough stock.',
                'code': 'insufficient_stock',
                'shortages': exc.shortages,
            },
            status=status.HTTP_409_CONFLICT,
        )
    if isinstance(exc, services.InvalidReservationState):
        return Response(
            {'detail': str(exc), 'code': 'invalid_state'}, status=status.HTTP_409_CONFLICT
        )
    if isinstance(exc, (services.ReservationNotFound, services.StockItemNotFound)):
        return Response({'detail': str(exc), 'code': 'not_found'}, status=status.HTTP_404_NOT_FOUND)
    if isinstance(exc, services.InvalidAdjustment):
        return Response(
            {'detail': str(exc), 'code': 'invalid_adjustment'}, status=status.HTTP_400_BAD_REQUEST
        )
    return exception_handler(exc, context)
