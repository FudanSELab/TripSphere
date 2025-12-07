from typing import Any, Literal, Self

from pydantic import BaseModel, Field, RootModel


class TextPart(BaseModel):
    text: str = Field(description="String content of the part.")
    kind: Literal["text"] = Field(default="text")
    metadata: dict[str, Any] | None = Field(default=None)


class FileWithUri(BaseModel):
    uri: str = Field(description="URI pointing to the file.")
    mime_type: str | None = Field(default=None, examples=["application/pdf"])
    name: str | None = Field(default=None, examples=["document.pdf"])


class FileWithBytes(BaseModel):
    bytes: str = Field(description="Base64-encoded file content.")
    mime_type: str | None = Field(default=None, examples=["application/pdf"])
    name: str | None = Field(default=None, examples=["document.pdf"])


class FilePart(BaseModel):
    file: FileWithUri | FileWithBytes = Field(...)
    kind: Literal["file"] = Field(default="file")
    metadata: dict[str, Any] | None = Field(default=None)

    @classmethod
    def from_uri(
        cls,
        uri: str,
        mime_type: str | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Self:
        """
        Arguments:
            uri: The URI pointing to the file.
            mime_type: Optional MIME type of the file.
            name: Optional name of the file.
            metadata: Optional metadata associated with the part.

        Returns:
            An instance of FilePart containing a FileWithUri.
        """
        file_with_uri = FileWithUri(uri=uri, mime_type=mime_type, name=name)
        return cls(file=file_with_uri, metadata=metadata)

    @classmethod
    def from_bytes(
        cls,
        bytes: str,
        mime_type: str | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Self:
        """
        Arguments:
            bytes: The base64-encoded file content.
            mime_type: Optional MIME type of the file.
            name: Optional name of the file.
            metadata: Optional metadata associated with the part.

        Returns:
            An instance of FilePart containing a FileWithBytes.
        """
        file_with_bytes = FileWithBytes(bytes=bytes, mime_type=mime_type, name=name)
        return cls(file=file_with_bytes, metadata=metadata)


class DataPart(BaseModel):
    data: dict[str, Any] = Field(description="Structured data content.")
    kind: Literal["data"] = Field(default="data")
    metadata: dict[str, Any] | None = Field(default=None)


class Part(RootModel[TextPart | FilePart | DataPart]):
    """
    Part can be one of TextPart, FilePart, or DataPart.
    """

    root: TextPart | FilePart | DataPart = Field(discriminator="kind")

    @classmethod
    def from_text(cls, text: str, metadata: dict[str, Any] | None = None) -> Self:
        """
        Arguments:
            text: The text content of the part.
            metadata: Optional metadata associated with the part.

        Returns:
            An instance of Part containing a TextPart.
        """
        return cls(TextPart(text=text, metadata=metadata))

    @classmethod
    def from_data(
        cls, data: dict[str, Any], metadata: dict[str, Any] | None = None
    ) -> Self:
        """
        Arguments:
            data: The structured data content of the part.
            metadata: Optional metadata associated with the part.

        Returns:
            An instance of Part containing a DataPart.
        """
        return cls(DataPart(data=data, metadata=metadata))
