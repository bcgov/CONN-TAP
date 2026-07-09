"""Single application error type.

Endpoints raise ``ApiError(status_code, detail)`` instead of ``HTTPException``;
it is translated to a JSON response by the handler registered in ``main.py``.
"""
from __future__ import annotations


class ApiError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
