from base64 import urlsafe_b64decode, urlsafe_b64encode

from bson import ObjectId


def encode_page_token(oid: ObjectId | None) -> str | None:
    if oid is None:
        return None
    return urlsafe_b64encode(oid.binary).decode("utf-8")


def decode_page_token(token: str | None) -> ObjectId | None:
    if token is None:
        return None
    binary = urlsafe_b64decode(token.encode("utf-8"))
    return ObjectId(binary)
