"""Stub the heavy third-party deps so the RBAC source modules import cleanly.

The unit-test job installs only ``pytest``/``pytest-cov`` (see
``.github/workflows/run-unit-tests.yml``), so ``fastapi``, ``pandas``, ``jwt``
and ``pydantic`` are not available. Mirroring the root ``conftest`` (which stubs
``alembic.op``/``sqlalchemy``), we inject just enough of each module for
``app.core.auth``, ``app.datasets.base`` and ``app.api.endpoints.datasets_api``
to be imported and their pure logic exercised.
"""
import sys
import types


def _ensure(name: str) -> types.ModuleType:
    mod = sys.modules.get(name)
    if mod is None:
        mod = types.ModuleType(name)
        sys.modules[name] = mod
    return mod


# ---- sqlalchemy (augment the root conftest's minimal stub) ------------------
_sa = _ensure("sqlalchemy")
if not hasattr(_sa, "text"):
    _sa.text = lambda s: s
_sa.create_engine = lambda *a, **k: object()

_orm = _ensure("sqlalchemy.orm")


class Session:  # noqa: D401 - marker type only
    ...


_orm.Session = Session
_orm.sessionmaker = lambda *a, **k: (lambda *a2, **k2: object())
_sa.orm = _orm


# ---- pandas -----------------------------------------------------------------
_pd = _ensure("pandas")


class _DataFrame:
    def __init__(self, *a, **k) -> None:
        ...


_pd.DataFrame = _DataFrame
# Dataset helpers call ``pd.notna`` to spot missing ids; tests feed ``None`` for
# those, so identity is a faithful enough stand-in for the real NaN check.
if not hasattr(_pd, "notna"):
    _pd.notna = lambda value: value is not None


# ---- jwt --------------------------------------------------------------------
_jwt = _ensure("jwt")


class PyJWTError(Exception):
    ...


class PyJWKClient:
    def __init__(self, *a, **k) -> None:
        ...


_jwt.PyJWTError = PyJWTError
_jwt.PyJWKClient = PyJWKClient
_jwt.decode = lambda *a, **k: {}


# ---- fastapi ----------------------------------------------------------------
_fa = _ensure("fastapi")


class HTTPException(Exception):
    def __init__(self, status_code: int | None = None, detail: str | None = None) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _identity_decorator(*a, **k):
    def wrap(fn):
        return fn

    return wrap


class APIRouter:
    def __init__(self, *a, **k) -> None:
        ...

    def get(self, *a, **k):
        return _identity_decorator()

    def post(self, *a, **k):
        return _identity_decorator()

    def put(self, *a, **k):
        return _identity_decorator()

    def delete(self, *a, **k):
        return _identity_decorator()

    def patch(self, *a, **k):
        return _identity_decorator()

    def include_router(self, *a, **k) -> None:
        ...


class FastAPI(APIRouter):
    def exception_handler(self, *a, **k):
        return _identity_decorator()

    def add_middleware(self, *a, **k) -> None:
        ...


class Request:
    def __init__(self, *a, **k) -> None:
        ...


class _Status:
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404


_fa.HTTPException = HTTPException
_fa.APIRouter = APIRouter
_fa.FastAPI = FastAPI
_fa.Request = Request
_fa.Depends = lambda dependency=None: dependency
_fa.Cookie = lambda default=None, **k: default
_fa.status = _Status()

_fa_responses = _ensure("fastapi.responses")


class JSONResponse:
    def __init__(self, status_code: int | None = None, content=None) -> None:
        self.status_code = status_code
        self.content = content


_fa_responses.JSONResponse = JSONResponse
_fa.responses = _fa_responses

_fa_mw = _ensure("fastapi.middleware")
_fa_cors = _ensure("fastapi.middleware.cors")
_fa_cors.CORSMiddleware = type("CORSMiddleware", (), {})
_fa_mw.cors = _fa_cors
_fa.middleware = _fa_mw

_fa_sec = _ensure("fastapi.security")


class HTTPAuthorizationCredentials:
    def __init__(self, scheme: str = "Bearer", credentials: str = "") -> None:
        self.scheme = scheme
        self.credentials = credentials


class HTTPBearer:
    def __init__(self, *a, **k) -> None:
        ...


_fa_sec.HTTPAuthorizationCredentials = HTTPAuthorizationCredentials
_fa_sec.HTTPBearer = HTTPBearer
_fa.security = _fa_sec


# ---- pydantic ---------------------------------------------------------------
_pyd = _ensure("pydantic")


class BaseModel:
    def __init__(self, **kwargs) -> None:
        self.__dict__.update(kwargs)

    def model_dump(self, *a, **k) -> dict:
        return dict(self.__dict__)


def _field_validator(*a, **k):
    def decorate(fn):
        return fn

    return decorate


if not hasattr(_pyd, "BaseModel"):
    _pyd.BaseModel = BaseModel
if not hasattr(_pyd, "field_validator"):
    _pyd.field_validator = _field_validator


# ---- pydantic_settings ------------------------------------------------------
_ps = _ensure("pydantic_settings")


class BaseSettings:
    def __init__(self, *a, **k) -> None:
        ...


_ps.BaseSettings = BaseSettings
_ps.SettingsConfigDict = lambda *a, **k: {}
