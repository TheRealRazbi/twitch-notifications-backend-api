from dataclasses import dataclass
from typing import Callable, Coroutine, TYPE_CHECKING

if TYPE_CHECKING:
    from value_types import TokenValidated
    from class_types import CRUD


@dataclass(kw_only=True)
class TokenCrudSetupConfig:
    token_file_name: str
    encrypt_key_file_name: str
    generate_token: Callable[[], Coroutine[None, None, any]]


@dataclass(kw_only=True)
class TokenManagerConfig:
    crud: 'CRUD'
    validate_token: Callable[[str], Coroutine[None, None, 'TokenValidated']]
    refresh_seconds_before: int = 86_400  # one day
    check_every_seconds: int = 3600  # one hour


