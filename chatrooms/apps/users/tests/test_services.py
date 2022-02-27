from chatrooms.apps.users.services import PasswordResetTokenGenerator
from chatrooms.apps.users.tests.factories import UserFactory


class TestPasswordResetTokenGenerator:

    async def test_make_token(self, mocker):
        mocker.patch.object(PasswordResetTokenGenerator, '_now_seconds', return_value=10)
        mocker.patch('hmac.HMAC.hexdigest', return_value='ABCD')

        user = await UserFactory()
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        assert token == 'a-ABCD'

    async def test_check_token(self):
        user = await UserFactory()
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        assert token_generator.check_token(user, token)

        user.email = f'not_a_{user.email}'
        assert not token_generator.check_token(user, token)

    async def test_check_token_timeout(self, mocker):
        now_seconds_mock = mocker.patch.object(PasswordResetTokenGenerator, '_now_seconds', return_value=42)

        user = await UserFactory()
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)

        now_seconds_mock.return_value = 42 + PasswordResetTokenGenerator.TIMEOUT
        assert token_generator.check_token(user, token)

        now_seconds_mock.return_value = 42 + PasswordResetTokenGenerator.TIMEOUT + 1  # timeout by 1 second
        assert not token_generator.check_token(user, token)
