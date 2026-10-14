import pytest
from users.models import CustomUser


@pytest.fixture
def user(db):
    return CustomUser.objects.create_user(
        email="u@test.com", first_name="Ivan",
        phone_number="+380501111111", password="pass12345",
    )
@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client