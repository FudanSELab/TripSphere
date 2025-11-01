from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import TypeAlias
from uuid import UUID

StrUUID: TypeAlias = str
PageToken: TypeAlias = str


def encode_page_token(uid: StrUUID | None) -> PageToken | None:
    if uid is None:
        return None
    return urlsafe_b64encode(UUID(uid).bytes).decode("utf-8")


def decode_page_token(token: PageToken | None) -> StrUUID | None:
    if token is None:
        return None
    binary = urlsafe_b64decode(token.encode("utf-8"))
    return str(UUID(bytes=binary))
