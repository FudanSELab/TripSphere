from typing import Any, Self

from pydantic import BaseModel, Field, RootModel, model_validator


class TextPart(BaseModel):
    text: str = Field(description="String content of the part.")
    metadata: dict[str, Any] | None = Field(default=None)


class FilePart(BaseModel):
    uri: str | None = Field(default=None, description="URI pointing to the file.")
    bytes: str | None = Field(default=None, description="Base64-encoded file content.")
    mime_type: str | None = Field(default=None, examples=["application/pdf"])
    name: str | None = Field(default=None, examples=["document.pdf"])
    metadata: dict[str, Any] | None = Field(default=None)

    @model_validator(mode="after")
    def check_bytes_xor_uri(self) -> Self:
        if self.bytes and self.uri:
            raise ValueError("Only one of 'bytes' or 'uri' should be provided.")
        if not (self.bytes or self.uri):
            raise ValueError("At least one of 'bytes' or 'uri' must be provided.")
        return self


class DataPart(BaseModel):
    data: dict[str, Any] = Field(description="Structured data content.")
    metadata: dict[str, Any] | None = Field(default=None)


class Part(RootModel[TextPart | FilePart | DataPart]):
    """
    Part can be one of TextPart, FilePart, or DataPart.
    """

    root: TextPart | FilePart | DataPart

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
    def from_file_uri(
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
            An instance of Part containing a FilePart.
        """
        return cls(FilePart(uri=uri, mime_type=mime_type, name=name, metadata=metadata))

    @classmethod
    def from_file_bytes(
        cls,
        bytes: str,
        mime_type: str | None = None,
        name: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Self:
        """
        Arguments:
            bytes: The Base64-encoded content of the file.
            mime_type: Optional MIME type of the file.
            name: Optional name of the file.
            metadata: Optional metadata associated with the part.

        Returns:
            An instance of Part containing a FilePart.
        """
        return cls(
            FilePart(bytes=bytes, mime_type=mime_type, name=name, metadata=metadata)
        )

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
