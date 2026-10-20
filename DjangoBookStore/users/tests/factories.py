import factory
from users.models import CustomUser


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomUser

    email = factory.Sequence(lambda n: f"user{n}@test.com")
    phone_number = factory.Sequence(lambda n: f"+3805000{n:05d}")
    first_name = "Test"
    password = "pass12345"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return model_class.objects.create_user(*args, **kwargs)
