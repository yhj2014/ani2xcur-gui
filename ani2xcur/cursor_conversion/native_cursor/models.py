"""光标转换共享数据结构。"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


@dataclass
class CursorImage:
    """单个名义尺寸下的光标图像。"""

    image: Image.Image
    hotspot: tuple[int, int]
    nominal: int

    def clone(self) -> "CursorImage":
        """复制当前光标图像。

        Returns:
            CursorImage: 复制后的光标图像。
        """
        return CursorImage(
            image=self.image.copy(),
            hotspot=self.hotspot,
            nominal=self.nominal,
        )


@dataclass
class CursorFrame:
    """包含一个或多个光标尺寸的动画帧。"""

    images: list[CursorImage]
    delay: float = 0.0

    def clone(self) -> "CursorFrame":
        """复制当前动画帧。

        Returns:
            CursorFrame: 复制后的动画帧。
        """
        return CursorFrame(
            images=[image.clone() for image in self.images],
            delay=self.delay,
        )
