from typing import Callable, Coroutine, TYPE_CHECKING

import cryptography.fernet
from cryptography.fernet import Fernet

from constants import EMPTY_TOKEN

if TYPE_CHECKING:
    from config import TokenCrudSetupConfig


class TokenCrud:
    __cryptography_key: bytes
    __generate_token: Callable[[], Coroutine[None, None, any]]
    __token_file_name: str

    @classmethod
    async def create_token_crud(cls, config: 'TokenCrudSetupConfig') -> 'TokenCrud':
        token_crud = cls()
        await token_crud._setup(config)
        return token_crud

    async def _setup(self, config: 'TokenCrudSetupConfig'):
        self.__generate_token = config.generate_token
        self.__cryptography_key = self._load_cryptography_key(config.encrypt_key_file_name)
        self.__token_file_name = config.token_file_name

    @staticmethod
    def _read_access_token(file_name: str) -> str:
        try:
            with open(file_name, 'rb') as file:
                return file.read().decode()
        except FileNotFoundError:
            return EMPTY_TOKEN

    @staticmethod
    def _store_access_token(*, token: str, key: bytes, file_name: str) -> None:
        f = Fernet(key)
        token = f.encrypt(token.encode())
        with open(file_name, 'wb') as file:
            file.write(token)

    @staticmethod
    def _generate_cryptography_key(file_name: str):
        key = Fernet.generate_key()
        with open(file_name, 'wb') as file:
            file.write(key)

    def _load_cryptography_key(self, file_name: str) -> bytes:
        try:
            with open(file_name, 'rb') as file:
                return file.read()
        except FileNotFoundError:
            self._generate_cryptography_key(file_name)
            return self._load_cryptography_key(file_name)

    async def create(self) -> None:
        token = await self.__generate_token()
        self._store_access_token(token=token, key=self.__cryptography_key, file_name=self.__token_file_name)

    async def update(self, token: str) -> None:
        self._store_access_token(token=token, key=self.__cryptography_key, file_name=self.__token_file_name)

    async def read(self):
        f = Fernet(self.__cryptography_key)
        try:
            return f.decrypt(self._read_access_token(self.__token_file_name)).decode()
        except cryptography.fernet.InvalidToken:
            return EMPTY_TOKEN

    async def delete(self):
        with open(self.__token_file_name, 'wb') as file:
            file.write(EMPTY_TOKEN.encode())
