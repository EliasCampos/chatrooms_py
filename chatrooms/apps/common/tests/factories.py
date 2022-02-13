import asyncio
import inspect

import factory


class TortoiseModelFactory(factory.Factory):

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return asyncio.create_task(cls._make_object_coroutine(model_class, *args, **kwargs))

    @staticmethod
    async def _make_object_coroutine(model_class, *args, **kwargs):
        for key, value in kwargs.items():
            if inspect.isawaitable(value):
                kwargs[key] = await value

        return await model_class.create(*args, **kwargs)

    @classmethod
    async def create_batch(cls, size, **kwargs):
        return [await cls.create(**kwargs) for _ in range(size)]
