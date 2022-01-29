from tortoise import fields, models


class Chat(models.Model):
    id = fields.UUIDField(pk=True)
    title = fields.CharField(max_length=160)
    created_at = fields.DatetimeField(auto_now_add=True)

    creator = fields.ForeignKeyField('models.User', related_name='own_chats')
    participants = fields.ManyToManyField('models.User', related_name='joined_chats')
