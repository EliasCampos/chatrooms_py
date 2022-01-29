from tortoise.queryset import QuerySet


def paginate_queryset(qs: QuerySet, page_size: int, page: int) -> QuerySet:
    page = max(page, 1)
    qs = qs.limit(page_size)
    if page > 1:
        qs = qs.offset(page_size * (page - 1))
    return qs

