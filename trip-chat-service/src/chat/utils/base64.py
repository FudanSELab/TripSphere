from base64 import urlsafe_b64decode, urlsafe_b64encode
from uuid import UUID


def encode_page_token(uid: UUID | None) -> str | None:
    if uid is None:
        return None
    return urlsafe_b64encode(uid.bytes).decode("utf-8")


def decode_page_token(token: str | None) -> UUID | None:
    if token is None:
        return None
    binary = urlsafe_b64decode(token.encode("utf-8"))
    return UUID(bytes=binary)
