import pytest

from orders.tasks import confirm_reservation, release_reservation
from services.warehouse_client import (
    InvalidReservationState,
    WarehouseNotFound,
    WarehouseUnavailable
)


def test_confirm_calls_warehouse(mock_warehouse):
    confirm_reservation(5)

    mock_warehouse.confirm.assert_called_once_with(5)


def test_release_calls_warehouse(mock_warehouse):
    release_reservation(5)

    mock_warehouse.release.assert_called_once_with(5)


@pytest.mark.parametrize('error', [WarehouseNotFound, InvalidReservationState])
def test_business_errors_are_logged_not_raised(mock_warehouse, error):
    mock_warehouse.confirm.side_effect = error('x')
    mock_warehouse.release.side_effect = error('x')

    confirm_reservation(5)
    release_reservation(5)


def test_unavailable_warehouse_is_retried(mock_warehouse):
    mock_warehouse.confirm.side_effect = WarehouseUnavailable('down')
    mock_warehouse.release.side_effect = WarehouseUnavailable('down')

    with pytest.raises(WarehouseUnavailable):
        confirm_reservation(5)
    with pytest.raises(WarehouseUnavailable):
        release_reservation(5)