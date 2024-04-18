import asyncio
from typing import TYPE_CHECKING, Callable, Coroutine

from constants import EMPTY_TOKEN

if TYPE_CHECKING:
    from config import TokenManagerConfig
    from class_types import CRUD
    from value_types import TokenValidated


class TokenManager:
    """Manages the token and refreshes it if needed."""
    _validate_token: Callable[[str], Coroutine[None, None, 'TokenValidated']]
    refresh_seconds_before: int
    check_every_seconds: int

    __crud: 'CRUD'
    __token = EMPTY_TOKEN
    __validate_token_task: asyncio.Task = None

    @classmethod
    async def generate_from_config(cls, config: 'TokenManagerConfig') -> 'TokenManager':
        token_manager = cls()
        await token_manager._setup(config)
        return token_manager

    async def _setup(self, config: 'TokenManagerConfig'):
        self.__crud = config.crud
        self.__token = await self.__crud.read()
        self._validate_token = config.validate_token
        self.refresh_seconds_before = config.refresh_seconds_before
        self.check_every_seconds = config.check_every_seconds

    async def _refresh_token_if_needed(self):
        while True:
            await asyncio.sleep(self.check_every_seconds)
            await self.validate_token()

    async def validate_token(self):
        if self.__token == EMPTY_TOKEN:
            await self._regenerate_token()
        response: 'TokenValidated' = await self._validate_token(self.__token)
        if response.expires_in < self.refresh_seconds_before:
            await self._regenerate_token()

    async def _regenerate_token(self):
        self.__token = await self.__crud.create()

    async def start_validating_tokens_periodically(self) -> None:
        """Periodically refreshes the token if it is about to expire. Doesn't hang the event loop."""
        if self.__validate_token_task is None:
            self.__validate_token_task = asyncio.create_task(self._refresh_token_if_needed())

    async def get_token(self) -> str:
        return self.__token
