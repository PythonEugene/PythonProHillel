from decouple import config
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

PERMS = ['reserve_stock', 'view_stockitem', 'view_reservation']


class Command(BaseCommand):
    help = 'Create the service account used by ProjectA'

    def handle(self, *args, **opts):
        User = get_user_model()
        phone = config('WAREHOUSE_SERVICE_USER')
        password = config('WAREHOUSE_SERVICE_PASSWORD')

        group, _ = Group.objects.get_or_create(name='service_accounts')
        group.permissions.set(Permission.objects.filter(codename__in=PERMS))

        user = User.objects.filter(phone_number=phone).first()
        if user is None:
            user = User.objects.create_user(
                email='service@bookstore.local',
                first_name='service',
                phone_number=phone,
                password=password,
            )
        else:
            user.set_password(password)
            user.save()
        user.groups.add(group)
        self.stdout.write(self.style.SUCCESS('Service user is ready'))
