"""Shared cursor conversion data structures."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


@dataclass
class CursorImage:
    """One cursor image for a nominal size."""

    image: Image.Image
    hotspot: tuple[int, int]
    nominal: int

    def clone(self) -> "CursorImage":
        return CursorImage(
            image=self.image.copy(),
            hotspot=self.hotspot,
            nominal=self.nominal,
        )


@dataclass
class CursorFrame:
    """One animation frame containing one or more cursor sizes."""

    images: list[CursorImage]
    delay: float = 0.0

    def clone(self) -> "CursorFrame":
        return CursorFrame(
            images=[image.clone() for image in self.images],
            delay=self.delay,
        )
