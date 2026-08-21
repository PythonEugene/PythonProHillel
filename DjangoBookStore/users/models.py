from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.base_user import BaseUserManager
from django.utils import timezone

SUPPORTED_LANGUAGES = [
    ('uk', 'Ukrainian'),
    ('en', 'English'),
]


class CustomUserManager(BaseUserManager):
    def create_user(self, email, first_name, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number is required')
        if not email:
            raise ValueError('Email is required')
        if not first_name:
            raise ValueError('First name is required')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            phone_number=phone_number,
            **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, first_name, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, first_name, phone_number, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name='Email', unique=True)
    date_of_birth = models.DateField(verbose_name='Date of Birth', blank=True, null=True)
    first_name = models.CharField(verbose_name='First Name', max_length=30, blank=True)
    last_name = models.CharField(verbose_name='Last Name', max_length=30, blank=True)
    profile_image = models.ImageField(verbose_name='Profile Image', upload_to='profile_pics/', null=True, blank=True)
    phone_number = models.CharField(verbose_name='Phone Number', max_length=20, blank=True, unique=True)
    is_staff = models.BooleanField(verbose_name='Is staff', default=False)
    is_active = models.BooleanField(verbose_name='Is active', default=True)
    date_joined = models.DateTimeField(verbose_name='Date of account creation', default=timezone.now)
    app_lang = models.CharField(verbose_name='Language', max_length=5, choices=SUPPORTED_LANGUAGES, default='uk')


    objects = CustomUserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email', 'first_name']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        permissions = [
            ('can_set_user_permissions', 'User can add permissions'),
            ('can_see_user_permissions', 'User can see permissions list')
        ]

    def __str__(self):
        return self.email

