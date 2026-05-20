"""光标转换使用的 Pillow 图像变换工具。"""

from __future__ import annotations

from math import ceil

from PIL import Image, ImageColor, ImageFilter

from ani2xcur.cursor_conversion.native_cursor.models import CursorFrame


def scale_frames(frames: list[CursorFrame], scale: float) -> None:
    """原地缩放每个光标图像和热点坐标。

    Args:
        frames (list[CursorFrame]): 要缩放的光标帧列表。
        scale (float): 缩放倍率。
    Raises:
        ValueError: 缩放倍率小于或等于 0 时抛出。
    """
    if scale <= 0:
        raise ValueError("Cursor scale must be greater than zero")

    for frame in frames:
        for cursor in frame.images:
            width, height = cursor.image.size
            new_size = (
                max(1, int(round(width * scale))),
                max(1, int(round(height * scale))),
            )
            cursor.image = cursor.image.convert("RGBA").resize(new_size, Image.Resampling.LANCZOS)
            hotspot_x, hotspot_y = cursor.hotspot
            cursor.hotspot = (
                max(0, int(round(hotspot_x * scale))),
                max(0, int(round(hotspot_y * scale))),
            )


def add_shadow_to_frames(
    frames: list[CursorFrame],
    *,
    color: str,
    opacity: int,
    radius: float,
    sigma: float,
    xoffset: float,
    yoffset: float,
) -> None:
    """为每个光标图像原地添加近似 Windows 风格的阴影。

    Args:
        frames (list[CursorFrame]): 要添加阴影的光标帧列表。
        color (str): 阴影颜色。
        opacity (int): 阴影不透明度。
        radius (float): 阴影半径比例。
        sigma (float): 阴影模糊比例。
        xoffset (float): 阴影水平偏移比例。
        yoffset (float): 阴影垂直偏移比例。
    """
    opacity = max(0, min(255, opacity))
    for frame in frames:
        for cursor in frame.images:
            image, hotspot = _add_shadow_to_image(
                cursor.image,
                cursor.hotspot,
                color=color,
                opacity=opacity,
                radius=radius,
                sigma=sigma,
                xoffset=xoffset,
                yoffset=yoffset,
            )
            cursor.image = image
            cursor.hotspot = hotspot


def _add_shadow_to_image(
    source: Image.Image,
    hotspot: tuple[int, int],
    *,
    color: str,
    opacity: int,
    radius: float,
    sigma: float,
    xoffset: float,
    yoffset: float,
) -> tuple[Image.Image, tuple[int, int]]:
    image = source.convert("RGBA")
    width, height = image.size
    offset_x = int(round(xoffset * width))
    offset_y = int(round(yoffset * height))
    blur_radius = max(radius * width, sigma * width, 0)
    margin = int(ceil(blur_radius * 2))

    left_pad = margin + max(0, -offset_x)
    top_pad = margin + max(0, -offset_y)
    right_pad = margin + max(0, offset_x)
    bottom_pad = margin + max(0, offset_y)
    canvas_size = (width + left_pad + right_pad, height + top_pad + bottom_pad)

    alpha = image.getchannel("A")
    shadow_alpha = Image.new("L", canvas_size, 0)
    shadow_alpha.paste(alpha, (left_pad + offset_x, top_pad + offset_y))
    if blur_radius > 0:
        shadow_alpha = shadow_alpha.filter(ImageFilter.GaussianBlur(blur_radius))
    if opacity < 255:
        shadow_alpha = shadow_alpha.point(lambda value: value * opacity // 255)

    color_values = ImageColor.getrgb(color)
    red, green, blue = color_values[0], color_values[1], color_values[2]
    shadow = Image.new("RGBA", canvas_size, (red, green, blue, 0))
    shadow.putalpha(shadow_alpha)

    result = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    result.alpha_composite(shadow)
    result.alpha_composite(image, dest=(left_pad, top_pad))

    bbox = result.getbbox()
    if bbox is None:
        return image, hotspot

    cropped = result.crop(bbox)
    hotspot_x = hotspot[0] + left_pad - bbox[0]
    hotspot_y = hotspot[1] + top_pad - bbox[1]
    hotspot_x = max(0, min(cropped.width, hotspot_x))
    hotspot_y = max(0, min(cropped.height, hotspot_y))
    return cropped, (hotspot_x, hotspot_y)
