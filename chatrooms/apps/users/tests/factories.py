import functools

from factory import Faker, LazyFunction

from chatrooms.apps.common.tests.factories import TortoiseModelFactory
from chatrooms.apps.users.models import User
from chatrooms.apps.users.security import get_password_hash


USER_PASSWORD = 'strongpassword'


class UserFactory(TortoiseModelFactory):
    email = Faker('email')
    password = LazyFunction(functools.partial(get_password_hash, USER_PASSWORD))

    class Meta:
        model = User
