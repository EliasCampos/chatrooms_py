from typing import Dict


class BadInputError(ValueError):

    def __init__(self, message: Dict[str, str]):
        self.message = message
        super().__init__(message)


class PermissionDeniedError(RuntimeError):

    def __init__(self, detail: str):
        self.detail = detail
