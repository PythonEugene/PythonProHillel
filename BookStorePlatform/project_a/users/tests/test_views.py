import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse
from users.tests.factories import UserFactory


def make_manager(*codenames):
    manager = UserFactory()
    manager.user_permissions.add(*Permission.objects.filter(codename__in=codenames))
    return manager


@pytest.mark.django_db
def test_permissions_page_opens_for_viewer(client):
    target = UserFactory()
    client.force_login(make_manager("can_see_user_permissions"))
    r = client.get(reverse("users:manage_permissions", args=[target.id]))
    assert r.status_code == 200
    assert r.context["target_user"] == target


@pytest.mark.django_db
def test_permissions_unknown_user_404(client):
    client.force_login(make_manager("can_see_user_permissions"))
    r = client.get(reverse("users:manage_permissions", args=[9999]))
    assert r.status_code == 404


@pytest.mark.django_db
def test_viewer_cannot_change_permissions(client):
    target = UserFactory()
    perm = Permission.objects.get(codename="add_book")
    client.force_login(make_manager("can_see_user_permissions"))
    r = client.post(
        reverse("users:manage_permissions", args=[target.id]), {"permissions": [perm.id]}
    )
    assert r.status_code == 403
    assert target.user_permissions.count() == 0


@pytest.mark.django_db
def test_permissions_are_replaced_not_added(client):
    target = UserFactory()
    old = Permission.objects.get(codename="add_book")
    new = Permission.objects.get(codename="change_book")
    target.user_permissions.add(old)
    client.force_login(make_manager("can_see_user_permissions", "can_set_user_permissions"))
    client.post(reverse("users:manage_permissions", args=[target.id]), {"permissions": [new.id]})
    assert list(target.user_permissions.all()) == [new]


@pytest.mark.django_db
def test_permissions_page_query_count(client, django_assert_max_num_queries):
    target = UserFactory()
    client.force_login(make_manager("can_see_user_permissions"))
    with django_assert_max_num_queries(15):
        client.get(reverse("users:manage_permissions", args=[target.id]))
