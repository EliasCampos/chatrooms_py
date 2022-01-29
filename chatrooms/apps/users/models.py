from tortoise import fields, models

from chatrooms.apps.users.security import generate_token


class User(models.Model):
    email = fields.CharField(max_length=100, unique=True)
    password = fields.CharField(max_length=100)
    date_join = fields.DatetimeField(auto_now_add=True)


class Token(models.Model):
    key = fields.CharField(max_length=40, pk=True)
    user = fields.OneToOneField(
        "models.User", related_name="auth_token",
    )

    @classmethod
    async def generate(cls, user: User):
        return await cls.create(key=generate_token(), user=user)
