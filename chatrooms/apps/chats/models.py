from tortoise import fields, models
from tortoise.expressions import Q


class Chat(models.Model):
    id = fields.UUIDField(pk=True)
    title = fields.CharField(max_length=160)
    created_at = fields.DatetimeField(auto_now_add=True)

    creator = fields.ForeignKeyField('models.User', related_name='own_chats')
    participants = fields.ManyToManyField('models.User', related_name='joined_chats')

    @classmethod
    def available_to_user(cls, user):
        return cls.filter(Q(creator=user) | Q(participants=user))


class ChatMessage(models.Model):
    text = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)
    is_deleted = fields.BooleanField(default=False)

    chat = fields.ForeignKeyField('models.Chat', related_name='messages')
    author = fields.ForeignKeyField('models.User', related_name='chat_messages')
