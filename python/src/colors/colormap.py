"""
Mapping of numeric values onto the colors of a palette.
This is the module a caller wants when all they need is a color for a value, so it deliberately
depends on nothing but the palette data -- no legend rendering, no image library.
"""
import warnings
from collections.abc import Sequence

from . import convert
from .palette import Palette


class ColorMap:
    """
    Maps numeric values in the range vmin to vmax onto the colors of a Palette
    """

    def __init__(self,
                 palette: 'Palette | str | Sequence[Sequence[int]]',
                 vmin: 'float | object | dict | None' = None,
                 vmax: float | None = None):
        """
        Default constructor
        :param palette: A Palette, a palette name, or a sequence of RGB integer triples
        :param vmin: Low end of the value range, or a Scale or dict carrying 'min' and 'max'
        :param vmax: High end of the value range, required when vmin is a number
        :raises ValueError: If the palette has no colors
        :raises TypeError: If the value range cannot be determined from the arguments
        """
        self.palette: Palette = self._as_palette(palette)

        # a palette we cannot index is a mistake worth catching here rather than on first lookup
        if not self.palette.color_values:
            raise ValueError(f'palette {self.palette.name!r} has no colors')

        # hold on to a Scale if we were given one, some callers read ColorMap.scale back out
        self._scale: object | None = None

        # a number means the caller passed an explicit range, anything else has to carry one
        if isinstance(vmin, (int, float)) and not isinstance(vmin, bool):
            if not isinstance(vmax, (int, float)) or isinstance(vmax, bool):
                raise TypeError('ColorMap(palette, vmin, vmax) requires both vmin and vmax')
            self.vmin: float = float(vmin)
            self.vmax: float = float(vmax)
        else:
            self.vmin, self.vmax = self._range_from(vmin, vmax)

    @property
    def n_colors(self) -> int:
        """
        Get the number of colors this map can return
        :return: Number of colors in the underlying palette
        """
        return self.palette.n_colors

    @property
    def scale(self) -> object:
        """
        Get a Scale describing this map's value range
        :return: The Scale this map was constructed with, or one built from vmin and vmax
        """
        # build a Scale on demand so the legacy attribute keeps working
        if self._scale is None:
            from .scale import Scale
            self._scale = Scale(min=self.vmin, max=self.vmax)
        return self._scale

    @staticmethod
    def _as_palette(palette: 'Palette | str | Sequence[Sequence[int]]') -> Palette:
        """
        Accept a palette given as an object, a name, or raw color values
        :param palette: A Palette, a palette name, or a sequence of RGB integer triples
        :return: A Palette instance
        """
        # already what we need
        if isinstance(palette, Palette):
            return palette

        # a name has to be looked up in the registry
        if isinstance(palette, str):
            return Palette(palette)

        # otherwise treat it as a sequence of RGB triples
        return Palette(color_values=[list(rgb) for rgb in palette])

    def _range_from(self, source: object, vmax: float | None) -> tuple[float, float]:
        """
        Read a value range out of a Scale, a mapping, or a pair of numbers
        :param source: A Scale, a mapping with 'min' and 'max' keys, or None
        :param vmax: High end of the range, which must be None when source carries its own range
        :return: The low and high end of the value range
        :raises TypeError: If the value range cannot be determined
        """
        # a mapping is the simple case, read the two keys we care about
        if isinstance(source, dict):
            low, high = source.get('min'), source.get('max')
        else:
            # anything exposing min and max works, which is how a legacy Scale is accepted
            low, high = getattr(source, 'min', None), getattr(source, 'max', None)
            if low is not None or high is not None:
                warnings.warn('ColorMap(palette, scale) is deprecated; '
                              'use ColorMap(palette, vmin, vmax) instead',
                              DeprecationWarning, stacklevel=3)
                self._scale = source

        # the range has to come from one place or the other, not both
        if vmax is not None:
            raise TypeError('ColorMap got a value range in its second argument and a third argument')
        if low is None or high is None:
            raise TypeError('ColorMap needs a value range: ColorMap(palette, vmin, vmax)')

        return float(low), float(high)

    @staticmethod
    def _normalize(x: float, x_min: float, x_max: float, n: int = 100) -> int:
        """
        Normalize a value between x_min and x_max to a 0-N scale.
        :param x: Value to normalize
        :param x_min: Minimum value of the range
        :param x_max: Maximum value of the range
        :param n: Maximum value of the output range (default: 100)
        :return: Normalized value between 0 and N-1
        """
        if x >= x_max:
            return n - 1
        elif x <= x_min:
            return 0
        else:
            normalized = ((x - x_min) / (x_max - x_min)) * (n - 1)
            return round(normalized)

    def index(self, x: float) -> int:
        """
        Get the palette index a value falls on
        :param x: Value to map
        :return: Index into the palette colors, from 0 to n_colors - 1
        """
        return self._normalize(x, self.vmin, self.vmax, self.palette.n_colors)

    def map_color(self, x: float, color_format: str = 'hex') -> str | list[int] | list[float]:
        """
        Get a color for a specific value using this map's palette and value range
        :param x: Value to map to a color
        :param color_format: Format to return, can be 'hex', 'int', 'float', defaults to 'hex'
        :return: Color value in the requested format
        :raises ValueError: If the color format is invalid
        """
        index: int = self._normalize(x, self.vmin, self.vmax, self.palette.n_colors)
        rgb: list[int] = self.palette.color_values[index]
        return convert.format_color(rgb, color_format)

    def legend(self, width: int | None = None, height: int | None = None, **scale_kwargs) -> bytes:
        """
        Render a legend graphic for this map, labelled with its own value range
        :param width: Width of the legend image in pixels
        :param height: Height of the legend image in pixels
        :param scale_kwargs: Scale attributes such as label, ticks, position, or precision
        :return: Bytes containing the PNG image of the legend
        :raises ModuleNotFoundError: If the optional legend extra is not installed
        """
        from .legend import render_legend
        from .scale import Scale

        # state the value range once, here, rather than making the caller repeat it on the scale
        scale_kwargs.setdefault('min', self.vmin)
        scale_kwargs.setdefault('max', self.vmax)
        scales: list[Scale] = [Scale(**scale_kwargs)] if scale_kwargs else []
        return render_legend(self.palette, width, height, scales=scales)


def color_at(palette: 'Palette | str | Sequence[Sequence[int]]',
             x: float,
             vmin: float,
             vmax: float,
             color_format: str = 'hex') -> str | list[int] | list[float]:
    """
    Get the color a single value maps to without keeping a ColorMap around
    :param palette: A Palette, a palette name, or a sequence of RGB integer triples
    :param x: Value to map to a color
    :param vmin: Low end of the value range
    :param vmax: High end of the value range
    :param color_format: Format to return, can be 'hex', 'int', 'float', defaults to 'hex'
    :return: Color value in the requested format
    """
    return ColorMap(palette, vmin, vmax).map_color(x, color_format)
