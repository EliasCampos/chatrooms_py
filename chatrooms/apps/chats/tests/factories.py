from factory import Faker, SubFactory

from chatrooms.apps.common.tests.factories import TortoiseModelFactory
from chatrooms.apps.chats.models import Chat, ChatMessage
from chatrooms.apps.users.tests.factories import UserFactory


class ChatFactory(TortoiseModelFactory):
    title = Faker('sentence')

    creator = SubFactory(UserFactory)

    class Meta:
        model = Chat


class ChatMessageFactory(TortoiseModelFactory):
    text = Faker('text', max_nb_chars=250)

    chat = SubFactory(ChatFactory)
    author = SubFactory(UserFactory)

    class Meta:
        model = ChatMessage
