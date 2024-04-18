from functools import partial

import aiohttp


async def status_200(response: aiohttp.ClientResponse) -> bool:
    return response.status == 200


async def has_key(response: aiohttp.ClientResponse, key: str) -> bool:
    """Use with partial() to create a function that checks if a key is in a json response"""
    return key in await response.json()


has_access_token = partial(has_key, key='access_token')
has_expires_in = partial(has_key, key='expires_in')
