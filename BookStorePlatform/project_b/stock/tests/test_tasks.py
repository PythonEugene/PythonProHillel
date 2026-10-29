import pytest
from unittest.mock import patch
from django.conf import settings
from stock.tasks import expire_reservations


@pytest.mark.django_db
def test_expire_reservations_task():
    settings.CELERY_TASK_ALWAYS_EAGER = True


with patch('stock.services.expire_reservations', return_value=2) as mock_expire:
    result = expire_reservations()

    assert result == 2
    mock_expire.assert_called_once()
