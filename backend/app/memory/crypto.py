"""Fernet encryption for utterance text at rest."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.config import get_settings


class CryptoError(RuntimeError):
    pass


class Cipher:
    def __init__(self, key: str) -> None:
        if not key:
            raise CryptoError(
                "FERNET_KEY is not set. Generate one: "
                'python -c "from cryptography.fernet import Fernet;'
                'print(Fernet.generate_key().decode())"'
            )
        try:
            self._f = Fernet(key.encode())
        except ValueError as e:
            raise CryptoError("FERNET_KEY is not a valid Fernet key") from e

    def encrypt(self, text: str) -> str:
        return self._f.encrypt(text.encode("utf-8")).decode("ascii")

    def decrypt(self, token: str) -> str:
        try:
            return self._f.decrypt(token.encode("ascii")).decode("utf-8")
        except InvalidToken as e:
            raise CryptoError("cannot decrypt: wrong FERNET_KEY or corrupted data") from e


def get_cipher() -> Cipher:
    return Cipher(get_settings().fernet_key)
