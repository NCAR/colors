"""
Legend graphic rendering.
This is the only module in the package that imports Pillow, which is an optional dependency,
so nothing here is reachable until a caller actually asks for an image.
"""
import logging
import os
from collections.abc import Sequence
from io import BytesIO

# what to tell a caller who has not installed the optional legend extra
PILLOW_REQUIRED: str = (
    'colors: legend rendering requires Pillow, which is an optional extra.\n'
    "Install it with:  pip install 'colors[legend]'\n"
    'Value-to-color mapping (colors.ColorMap) works without it.'
)


def require_pillow() -> None:
    """
    Check that Pillow is importable before anything relies on it
    :raises ModuleNotFoundError: If Pillow is missing or cannot be imported
    """
    # catch ImportError rather than probing for the package, because a Pillow whose native
    # libraries are missing is just as unusable as one that was never installed
    try:
        from PIL import Image, ImageDraw, ImageFont  # noqa: F401
    except ImportError as e:
        raise ModuleNotFoundError(PILLOW_REQUIRED) from e


# fail with useful guidance rather than a bare ImportError from somewhere deeper
require_pillow()

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageDraw import ImageDraw as ImgDraw

from .palette import Palette
from .scale import Scale

# default legend dimensions in pixels
DEFAULT_WIDTH: int = 800
DEFAULT_HEIGHT: int = 600

# how far a tick mark extends into the scale band, in pixels
TICK_LENGTH: int = 10

# tick labels are drawn at a fraction of the scale's font size
TICK_FONT_RATIO: float = 0.7

log = logging.getLogger('colors')


def font_dir() -> str:
    """
    Get the font directory from this package
    :return: Path to the directory holding the packaged fonts
    """
    from .resources import fonts
    return os.path.dirname(fonts.__file__)


def resolve_font(font_family: str | None, font_size: float) -> ImageFont.FreeTypeFont:
    """
    Load a packaged font, falling back to a default if the requested family is unavailable
    :param font_family: Name of the font family, matched against the packaged .ttf files
    :param font_size: Size of the font in points
    :return: Font definition
    """
    directory: str = font_dir()
    try:
        font_file: str = f'{directory}/{str(font_family).lower()}.ttf'
        return ImageFont.truetype(font_file, font_size)
    except Exception as e:
        log.warning('WARN: Failed to load requested font family, using a default')
        log.warning(e)
        return ImageFont.truetype(f'{directory}/arial.ttf', font_size)


class ScaleRenderer:
    """
    Draws one Scale onto an image. All of the mutable drawing state lives here rather than on
    the Scale, so a Scale stays a plain description that can be reused across renders.
    """

    def __init__(self, scale: Scale):
        """
        Default constructor
        :param scale: The scale configuration to draw
        """
        self.scale = scale

        # drawing state, valid only for the duration of a draw call
        self._image: Image.Image | None = None
        self._draw: ImgDraw | None = None
        self._x: int = 0  # x offset in parent image to draw the scale
        self._y: int = 0  # y offset in parent image to draw the scale
        self._width: int = 0
        self._height: int = 0

    @property
    def font(self) -> ImageFont.FreeTypeFont:
        """
        Get the font to use for the scale label
        :return: Font definition
        """
        return resolve_font(self.scale.font_family, self.scale.font_size)

    @property
    def smaller_font(self) -> ImageFont.FreeTypeFont:
        """
        Get a smaller font, used for the tick labels
        :return: Font definition
        """
        return resolve_font(self.scale.font_family, self.scale.font_size * TICK_FONT_RATIO)

    def draw(self, image: Image.Image) -> None:
        """
        Draw the scale onto an image
        :param image: The image to draw on
        """
        # get the bounding box size for this section
        self._image = image
        scale_bbox = self._get_scale_bbox(ImageDraw.Draw(image))

        # create a new draw for only the scale area
        scale_area_img = self._image.crop(scale_bbox)
        self._draw = ImageDraw.Draw(scale_area_img)

        # fill the background of the scale area
        self._fill_background()

        # add the center label
        self._add_label()

        # add the tick marks
        self._add_tick_marks()

        # add the tick mark labels
        self._add_tick_labels()

        # paste the scale image on top of the base image
        self._image.paste(scale_area_img, (scale_bbox[0], scale_bbox[1]))

        # the drawing state is meaningless outside this call
        self._draw = None

    def _get_scale_bbox(self, draw: ImgDraw) -> tuple[int, int, int, int]:
        """
        Get the bounding box coordinates of the scale area
        :param draw: Draw object to get the text bbox
        :return: x1, y1, x2, y2 describes the extent of the scale area
        """
        # get the minimum box size to fit the text, measuring a placeholder if there is no label
        measured: str = self.scale.label if self.scale.label else '0'
        label_bbox = draw.textbbox((0, 0), measured, font=self.font)
        self._width = int(label_bbox[2] - label_bbox[0])
        self._height = int(label_bbox[3] - label_bbox[1])

        # increase the box size to fix the value labels at .7x font size
        self._height += int(label_bbox[3] - label_bbox[1]) + 8

        # add padding
        self._height += self.scale.padding[0] + self.scale.padding[2]
        self._width += self.scale.padding[1] + self.scale.padding[3]

        # add margin
        self._height += self.scale.margin[0] + self.scale.margin[2]
        self._width += self.scale.margin[1] + self.scale.margin[3]

        # reposition the origin depending on the origin value
        self._x = 0
        self._y = 0 if self.scale.position == 'top' else self._image.size[1] - self._height

        # we really want the full width of the image anyway it turns out
        self._width = self._image.size[0]

        return self._x, self._y, self._x + self._width, self._y + self._height

    def _fill_background(self) -> None:
        """
        Fill the scale area with the background color
        """
        # choose the background color
        color = self.scale.background_color
        if color is None:
            color = (0, 0, 0, 0)  # transparent will erase the area

        # fill the scale area with the background color
        self._draw.rectangle((0, 0, self._width, self._height), fill=tuple(color))

    def _add_label(self) -> None:
        """
        Add the label to the center of the scale
        """
        # nothing to do if the label is not defined
        if self.scale.label is None:
            return

        self._draw.text(self._label_xy, self.scale.label, anchor=self._label_anchor,
                        fill=tuple(self.scale.color), font=self.font)

    def _add_tick_marks(self) -> None:
        """
        Add tick marks to the scale
        """
        # nothing to do if ticks are disabled
        if not self.scale.ticks:
            return

        tick_proximal: int = 0 if self.scale.position == 'bottom' else self._height
        tick_height: int = TICK_LENGTH * (1 if self.scale.position == 'bottom' else -1)
        y1 = min(tick_proximal, tick_proximal + tick_height)
        y2 = max(tick_proximal, tick_proximal + tick_height)
        for x in self._tick_x_positions():
            box = self._fixbox((x - 1, y1, x + 1, y2))
            self._draw.rectangle(box, fill=tuple(self.scale.color))

    def _add_tick_labels(self) -> None:
        """
        Add tick marks labels to the scale
        """
        # nothing to do without a value range and a tick count
        values: list[float] = self.scale.tick_values()
        if not values:
            return

        tick_proximal: int = 0 if self.scale.position == 'bottom' else self._height
        tick_height: int = TICK_LENGTH * (1 if self.scale.position == 'bottom' else -1)
        y: int = tick_height + tick_proximal

        font = self.smaller_font
        fvs: list[str] = [f'{v:.{self.scale.precision}f}' for v in values]
        for i, x in enumerate(self._tick_x_positions()):
            v: str = fvs[i]
            x = self._correct_label_x_position(x, v, font)
            self._draw.text((x, y), v, font=font, anchor=self._tick_anchor,
                            fill=tuple(self.scale.color))

    def _tick_x_positions(self) -> list[int]:
        """
        Get the x position of each tick mark across the scale
        :return: One x position per tick, evenly spaced across the full width
        """
        ticks: int = self.scale.ticks or 0

        # a single tick has nothing to be spaced against, so leave it at the origin
        divisor: int = max(ticks - 1, 1)
        return [i * self._width // divisor for i in range(ticks)]

    def _correct_label_x_position(self, x: int, v: str, f: ImageFont.FreeTypeFont) -> int:
        """
        Check if the label is going to be off-image with this x position, and correct it if so
        :param x: Check if this x value is ok
        :param v: Label string
        :param f: Font we are using
        :return: An x value that will not push the label off-image
        """
        bbox = self._draw.textbbox((x, 0), v, font=f, anchor='ma')
        min_x, max_x = int(bbox[0]), int(bbox[2])

        if min_x < 0 and max_x > self._width:
            return x  # can't help your font/string is too large

        if min_x < 0:
            return x - min_x + 1

        if max_x > self._width:
            return x - (max_x - self._width + 1)

        return x

    def _fixbox(self, bbox) -> tuple[int, int, int, int]:
        """
        Make sure the points are all on the canvas, shift it around if not
        :param bbox: The box to correct, as x1, y1, x2, y2
        :return: A box whose points all fall inside the scale area
        """
        dx: int = 0
        dy: int = 0
        if bbox[0] < 0:
            dx = 0 - bbox[0]
        if bbox[2] >= self._width:
            dx = self._width - bbox[2] - 1
        if bbox[1] < 0:
            dy = 0 - bbox[1]
        if bbox[3] >= self._height:
            dy = self._height - bbox[3] - 1

        return bbox[0] + dx, bbox[1] + dy, bbox[2] + dx, bbox[3] + dy

    @property
    def _label_xy(self) -> tuple[int, int]:
        """
        Get the x, y position for the label
        :return: x, y position for the label
        """
        if self.scale.position == 'top':
            y = self.scale.margin[0] + self.scale.padding[0]
        else:
            y = self._height - self.scale.margin[2] - self.scale.padding[2] - 1

        return self._width // 2, y

    @property
    def _label_anchor(self) -> str:
        """
        Get the label anchor position for the draw.text function
        :return: Label anchor position
        """
        return {
            'top': 'ma',    # top-center
            'bottom': 'md'  # bottom-center
        }.get(self.scale.position, 'md')

    @property
    def _tick_anchor(self) -> str:
        """
        Get the tick label anchor position for the draw.text function
        :return: Label anchor position
        """
        return {
            'top': 'md',    # bottom-center
            'bottom': 'ma'  # top-center
        }.get(self.scale.position, 'ma')


class Legend:
    """
    Renders a Palette, optionally annotated with Scales, into a legend graphic
    """

    def __init__(self, palette: Palette, scales: Sequence[Scale] = ()):
        """
        Default constructor
        :param palette: The palette to render as a gradient
        :param scales: Scales to draw on top of the gradient
        """
        self.palette = palette
        self.scales: list[Scale] = list(scales)

    def to_image(self, width: int | None = None, height: int | None = None) -> Image.Image:
        """
        Render the legend as an image
        :param width: Width of the legend image in pixels
        :param height: Height of the legend image in pixels
        :return: The rendered image
        """
        # make sure we have good dimensions
        full_width: int = DEFAULT_WIDTH if width is None else width
        full_height: int = DEFAULT_HEIGHT if height is None else height

        # create an empty image of size width, height. divide the number of pixels by the width
        image = Image.new('RGBA', (full_width, full_height), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)

        # create the dimensions of solid color fills
        segment_width: float = full_width / (len(self.palette.color_values))
        segment_height: int = full_height

        # fill rectangles for each segment of the color palette
        for i, color in enumerate(self.palette.color_values):
            # draw a vertical line of the color
            rect = (i * segment_width, 0, (i + 1) * segment_width, segment_height)
            draw.rectangle(rect, fill=tuple(color))

        # draw any scales on top of the palette
        for scale in self.scales:
            ScaleRenderer(scale).draw(image)

        return image

    def to_png(self, width: int | None = None, height: int | None = None) -> bytes:
        """
        Render the legend as a PNG
        :param width: Width of the legend image in pixels
        :param height: Height of the legend image in pixels
        :return: Bytes containing the PNG image of the legend
        """
        # create and return the PNG bytes
        buffer = BytesIO()
        self.to_image(width, height).save(buffer, format='PNG')
        return buffer.getvalue()


def render_legend(palette: Palette,
                  width: int | None = None,
                  height: int | None = None,
                  scales: Sequence[Scale] = ()) -> bytes:
    """
    Render a legend graphic for a palette
    :param palette: The palette to render as a gradient
    :param width: Width of the legend image in pixels
    :param height: Height of the legend image in pixels
    :param scales: Scales to draw on top of the gradient
    :return: Bytes containing the PNG image of the legend
    """
    return Legend(palette, scales).to_png(width, height)
