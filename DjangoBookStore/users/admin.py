from django.contrib import admin
from .models import CustomUser
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

admin.site.register(CustomUser)
# admin.site.unregister(User)
admin.site.register(ContentType)
