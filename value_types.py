from dataclasses import dataclass


@dataclass
class TokenValidated:
    expires_in: int
    access_token: str = ''
    client_id: str = ''
    scopes: list[str] = None
