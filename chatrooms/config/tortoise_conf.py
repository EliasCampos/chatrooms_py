from chatrooms.config import settings

TORTOISE_ORM = {
    "connections": {"default": settings.DATABASE_URI},
    "apps": {
        "models": {
            "models": settings.APPS_MODELS,
            "default_connection": "default",
        }
    },
}
