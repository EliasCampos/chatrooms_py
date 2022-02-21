from typing import List

from chatrooms.apps.common.pagination import PageNumberPagination
from chatrooms.apps.chats.schemas import ChatDetail, ChatOwn, ChatMessageDetail


class ChatPagination(PageNumberPagination):
    results: List[ChatDetail]


class ChatOwnPagination(PageNumberPagination):
    results: List[ChatOwn]


class ChatMessagePagination(PageNumberPagination):
    results: List[ChatMessageDetail]
