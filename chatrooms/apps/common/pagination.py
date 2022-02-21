import asyncio
import math
from typing import get_type_hints, Optional, List

from pydantic import BaseModel
from tortoise.queryset import QuerySet


class PageNumberPagination(BaseModel):
    count: int
    next: Optional[int]
    previous: Optional[int]
    results: List[BaseModel]

    @classmethod
    async def paginate_queryset(cls, qs: QuerySet, page_size: int, page: int) -> 'PageNumberPagination':
        page = max(page, 1)
        base_qs = qs
        qs = qs.limit(page_size)
        if page > 1:
            qs = qs.offset(page_size * (page - 1))

        count, items = await asyncio.gather(base_qs.count(), qs)

        max_pages = math.ceil(count / page_size)
        next_page = page + 1 if page + 1 <= max_pages else None
        previous_page = min(page - 1, max_pages) if page > 1 else None

        base_schema = get_type_hints(cls)['results'].__args__[0]
        results = [base_schema.from_orm(item) for item in items]

        return cls(
            count=count,
            next=next_page,
            previous=previous_page,
            results=results,
        )
