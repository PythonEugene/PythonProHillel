from django.apps import AppConfig
from django.db.models.signals import post_migrate

# group name -> permission codenames
GROUPS = {
    'Service': ['reserve_stock', 'view_stockitem', 'view_reservation'],
    'Warehouse Manager': [
        'adjust_stock',
        'view_reports',
        'view_stockitem',
        'view_reservation',
        'view_stockmovement',
    ],
    'Analyst': [
        'view_reports',
        'view_stockitem',
        'view_reservation',
        'view_stockmovement',
    ],
}


def create_groups(sender, **kwargs):
    """Create the warehouse groups and give them their permissions."""
    from django.contrib.auth.models import Group, Permission

    for name, codenames in GROUPS.items():
        group, _created = Group.objects.get_or_create(name=name)
        permissions = Permission.objects.filter(
            content_type__app_label='stock', codename__in=codenames
        )
        group.permissions.set(permissions)


class StockConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stock'

    def ready(self):
        post_migrate.connect(create_groups, sender=self)
