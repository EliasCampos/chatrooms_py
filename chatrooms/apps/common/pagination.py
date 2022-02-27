import asyncio
import math
from typing import get_type_hints, Optional, List
from urllib.parse import urljoin, urlencode

from fastapi import Request
from pydantic import BaseModel
from tortoise.queryset import QuerySet


class PageNumberPagination(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[BaseModel]

    @classmethod
    async def paginate_queryset(
            cls,
            qs: QuerySet,
            page_size: int,
            page: int,
            request: Request
    ) -> 'PageNumberPagination':
        page = max(page, 1)
        base_qs = qs
        qs = qs.limit(page_size)
        if page > 1:
            qs = qs.offset(page_size * (page - 1))

        count, items = await asyncio.gather(base_qs.count(), qs)

        max_pages = math.ceil(count / page_size)
        url = urljoin(str(request.base_url), request.url.path)
        if page + 1 > max_pages:
            next_page = None
        else:
            query_params = {**request.query_params, 'page': page + 1}
            next_page = '?'.join([url, urlencode(query_params)])

        if page <= 1:
            previous_page = None
        else:
            query_params = {**request.query_params, 'page': min(page - 1, max_pages)}
            previous_page = '?'.join([url, urlencode(query_params)])

        base_schema = get_type_hints(cls)['results'].__args__[0]
        results = [base_schema.from_orm(item) for item in items]

        return cls(
            count=count,
            next=next_page,
            previous=previous_page,
            results=results,
        )
