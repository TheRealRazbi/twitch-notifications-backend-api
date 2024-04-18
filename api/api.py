import traceback
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Coroutine, Union

import aiohttp

from api.token_crud import TokenCrud
from api.token_manager import TokenManager
from api.validators import status_200, has_access_token, has_expires_in
from config import TokenManagerConfig, TokenCrudSetupConfig
from constants import TOKEN_FILE_NAME, ENCRYPT_KEY_FILE_NAME
from value_types import TokenValidated

if TYPE_CHECKING:
    pass


@dataclass(kw_only=True)
class RetryRequest:
    session: aiohttp.ClientSession
    method: str
    url: str
    is_valid: list[Callable[[aiohttp.ClientResponse], Coroutine[None, None, bool]]] = field(default_factory=list)
    headers: dict = field(default_factory=dict)
    params: list[tuple[str, str]] = field(default_factory=list)
    retries: int = 5
    timeout: int = 10
    critical: bool = False

    def __post_init__(self):
        self.is_valid.insert(0, status_200)

    async def request(self):
        for _ in range(self.retries):
            try:
                async with self.session.request(self.method, self.url, headers=self.headers,
                                                params=self.params) as response:
                    if any([not await is_valid(response) for is_valid in self.is_valid]):
                        continue
                    return await response.json()
            except Exception as e:
                traceback.print_exc()
                print(f"Failed to get a valid response from {self.url}. Exception: {e}. Retrying...")
        if self.critical:
            raise Exception(f"Failed to get a valid response from {self.url}. Last response: {response}")
        return None


class API:
    __token_manager: 'TokenManager'

    def __init__(self, client_id, client_secret):
        self._client_id = client_id
        self._client_secret = client_secret

    async def setup(self):
        crud_config = TokenCrudSetupConfig(token_file_name=TOKEN_FILE_NAME,
                                           encrypt_key_file_name=ENCRYPT_KEY_FILE_NAME,
                                           generate_token=self.generate_access_token)
        crud = await TokenCrud.create_token_crud(crud_config)
        token_manager_config = TokenManagerConfig(crud=crud, validate_token=self.validate_access_token)
        self.__token_manager = await TokenManager.generate_from_config(token_manager_config)
        await self.__token_manager.validate_token()
        await self.__token_manager.start_validating_tokens_periodically()

    async def generate_access_token(self) -> str:
        headers = {
            'Content-Type': 'application/json',
        }
        params = {
            'client_id': self._client_id,
            'client_secret': self._client_secret,
            'grant_type': 'client_credentials'
        }
        url = 'https://id.twitch.tv/oauth2/token'
        async with aiohttp.ClientSession() as session:
            response = await RetryRequest(session=session, method='POST', url=url, headers=headers,
                                          params=list(params.items()), is_valid=[has_access_token],
                                          critical=True).request()
            return response['access_token']

    async def validate_access_token(self, access_token) -> 'TokenValidated':
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Client-ID": self._client_id
        }
        url = "https://id.twitch.tv/oauth2/validate"
        async with aiohttp.ClientSession() as session:
            response = await RetryRequest(session=session, method='GET', url=url, headers=headers,
                                          is_valid=[has_expires_in], critical=True).request()
            return TokenValidated(**response)

    async def get_live_streamers(self, streamers: list[str]) -> Union[None, list[dict]]:
        if len(streamers) > 100:
            raise Exception("Cannot get more than 100 streamers at once")
        headers = {
            'Authorization': f'Bearer {await self.__token_manager.get_token()}',
            'Client-ID': self._client_id
        }
        params = [('user_login', user_login) for user_login in streamers]
        url = 'https://api.twitch.tv/helix/streams'

        async with aiohttp.ClientSession() as session:
            response = await RetryRequest(session=session, method='GET', url=url, headers=headers,
                                          params=params).request()
            return response.get('data')
