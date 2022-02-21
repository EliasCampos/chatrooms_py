from typing import Dict


class BadInputError(ValueError):

    def __init__(self, detail: Dict[str, str]):
        self.detail = detail
        super().__init__(detail)


class PermissionDeniedError(RuntimeError):

    def __init__(self, detail: str):
        self.detail = detail
