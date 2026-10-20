import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from users.models import CustomUser

pytestmark = pytest.mark.django_db

REGISTER = {
    'email': 'api@test.com',
    'phone_number': '+380509999999',
    'first_name': 'Api',
    'password': 'Str0ngPass!234',
}


def obtain_tokens(client, user):
    """Log in through the real JWT endpoint (password of the `user` fixture)."""
    return client.post(
        reverse('api:token_obtain_pair'),
        {'phone_number': user.phone_number, 'password': 'pass12345'},
        format='json',
    )


# Generated with AI, reviewed and modified
def test_register_creates_user_without_exposing_password(api_client):
    r = api_client.post(reverse('api:register'), REGISTER, format='json')
    assert r.status_code == 201
    assert 'password' not in r.data
    created = CustomUser.objects.get(email=REGISTER['email'])
    assert created.check_password(REGISTER['password'])
    assert created.password != REGISTER['password']  # stored as a hash


# Generated with AI, reviewed and modified
def test_register_duplicate_user_is_rejected(api_client):
    api_client.post(reverse('api:register'), REGISTER, format='json')
    r = api_client.post(reverse('api:register'), REGISTER, format='json')
    assert r.status_code == 400
    assert 'email' in r.data
    assert CustomUser.objects.count() == 1


# Generated with AI, reviewed and modified
def test_register_weak_password_is_rejected(api_client):
    r = api_client.post(
        reverse('api:register'), {**REGISTER, 'password': '12345678'}, format='json'
    )
    assert r.status_code == 400
    assert 'password' in r.data


# Generated with AI, reviewed and modified
def test_register_requires_first_name(api_client):
    data = {k: v for k, v in REGISTER.items() if k != 'first_name'}
    r = api_client.post(reverse('api:register'), data, format='json')
    assert r.status_code == 400
    assert 'first_name' in r.data


# Generated with AI, reviewed and modified
def test_token_obtain_returns_access_and_refresh(api_client, user):
    r = obtain_tokens(api_client, user)
    assert r.status_code == 200
    assert {'access', 'refresh'} <= set(r.data)


# Generated with AI, reviewed and modified
def test_token_obtain_wrong_password(api_client, user):
    r = api_client.post(
        reverse('api:token_obtain_pair'),
        {'phone_number': user.phone_number, 'password': 'wrong'},
        format='json',
    )
    assert r.status_code == 401


# Generated with AI, reviewed and modified
def test_token_refresh_returns_new_access(api_client, user):
    refresh = obtain_tokens(api_client, user).data['refresh']
    r = api_client.post(reverse('api:token_refresh'), {'refresh': refresh}, format='json')
    assert r.status_code == 200
    assert 'access' in r.data


# Generated with AI, reviewed and modified
def test_token_verify_accepts_valid_token(api_client, user):
    access = obtain_tokens(api_client, user).data['access']
    r = api_client.post(reverse('api:token_verify'), {'token': access}, format='json')
    assert r.status_code == 200


# Generated with AI, reviewed and modified
def test_token_verify_rejects_garbage(api_client):
    r = api_client.post(reverse('api:token_verify'), {'token': 'garbage'}, format='json')
    assert r.status_code == 401


# Generated with AI, reviewed and modified
def test_me_requires_authentication(api_client):
    assert api_client.get(reverse('api:me')).status_code == 401


# Generated with AI, reviewed and modified
def test_me_returns_profile_for_jwt_user(api_client, user):
    access = obtain_tokens(api_client, user).data['access']
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
    r = client.get(reverse('api:me'))
    assert r.status_code == 200
    assert r.data['phone_number'] == user.phone_number
    assert 'password' not in r.data


# Generated with AI, reviewed and modified
def test_invalid_bearer_token_is_rejected():
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Bearer not-a-real-token')
    assert client.get(reverse('api:me')).status_code == 401
