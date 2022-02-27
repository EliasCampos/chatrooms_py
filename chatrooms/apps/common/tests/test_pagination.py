from typing import List

from fastapi import Request
from pydantic import BaseModel

from chatrooms.apps.common.pagination import PageNumberPagination
from chatrooms.apps.users.models import User
from chatrooms.apps.users.tests.factories import UserFactory


class UserTest(BaseModel):
    id: int

    class Config:
        orm_mode = True


class UserPageNumberPagination(PageNumberPagination):
    results: List[UserTest]


async def test_paginate_queryset():
    users = await UserFactory.create_batch(size=5)
    request = Request(scope={
        'type': 'http',
        'scheme': 'http',
        'server': ('127.0.0.1', 3000),
        'path': '/api/v1/test',
        'query_string': b'name=John&page=1&age=33',
        'headers': {},
    })

    result = await UserPageNumberPagination.paginate_queryset(
        qs=User.all().order_by('id'),
        page_size=2,
        page=1,
        request=request,
    )
    assert result.count == 5
    assert result.next == "http://127.0.0.1:3000/api/v1/test?name=John&page=2&age=33"
    assert result.previous is None
    assert len(result.results) == 2
    assert result.results[0].id == users[0].id
    assert result.results[1].id == users[1].id

    result = await UserPageNumberPagination.paginate_queryset(
        qs=User.all().order_by('id'),
        page_size=2,
        page=2,
        request=request,
    )
    assert result.count == 5
    assert result.next == "http://127.0.0.1:3000/api/v1/test?name=John&page=3&age=33"
    assert result.previous == "http://127.0.0.1:3000/api/v1/test?name=John&page=1&age=33"
    assert len(result.results) == 2
    assert result.results[0].id == users[2].id
    assert result.results[1].id == users[3].id

    result = await UserPageNumberPagination.paginate_queryset(
        qs=User.all().order_by('id'),
        page_size=2,
        page=3,
        request=request,
    )
    assert result.count == 5
    assert result.next is None
    assert result.previous == "http://127.0.0.1:3000/api/v1/test?name=John&page=2&age=33"
    assert len(result.results) == 1
    assert result.results[0].id == users[4].id
