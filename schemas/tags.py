from typing import TypedDict


class Tag(TypedDict):
    """A tag record as stored in TAGS and returned by the API."""

    id: int
    name: str


REQUIRED_FIELDS: tuple[str, ...] = ("name",)
