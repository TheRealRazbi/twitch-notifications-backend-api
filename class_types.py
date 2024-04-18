from typing import Protocol


class CRUD(Protocol):
    async def create(self) -> any:
        ...

    async def read(self) -> any:
        ...

    async def update(self, value: any) -> any:
        ...

    async def delete(self) -> any:
        ...
