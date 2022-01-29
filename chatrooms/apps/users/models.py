from tortoise import fields, models

from chatrooms.apps.users.security import generate_token, verify_password


class User(models.Model):
    email = fields.CharField(max_length=100, unique=True)
    password = fields.CharField(max_length=100)
    date_join = fields.DatetimeField(auto_now_add=True)

    def check_password(self, password):
        return verify_password(plain_password=password, hashed_password=self.password)


class Token(models.Model):
    key = fields.CharField(max_length=40, pk=True)
    user = fields.OneToOneField(
        "models.User", related_name="auth_token",
    )

    @classmethod
    async def generate(cls, user: User):
        return await cls.create(key=generate_token(), user=user)
