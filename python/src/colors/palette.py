"""
Color palettes: a named list of RGB colors, plus the operations that produce another palette.
Rendering a palette lives in colors.legend, and mapping values onto one lives in colors.colormap.
"""
from collections.abc import Sequence
from typing import TYPE_CHECKING

from . import convert
from . import registry
from .interp import interp, linspace, stack

# imported for type checking only, because colors.colormap imports this module
if TYPE_CHECKING:
    from .colormap import ColorMap


class Palette:
    """
    Class that handles color palettes and associated operations
    """
    # palette definitions, looked up on demand from the shared registry
    PALETTES: registry.PaletteRegistry = registry.PALETTES

    def __init__(self, name: str = None, default: str = None,
                 *, color_values: Sequence[Sequence[int]] | None = None):
        """
        Default constructor
        :param name: Palette name to load
        :param default: Backup palette to load if first is not found
        :param color_values: Use these RGB values instead of looking the name up
        """
        # take the colors we were handed, otherwise resolve the name against the registry
        if color_values is not None:
            self.name: str | None = name
            self.color_values: list[list[int]] | None = [list(rgb) for rgb in color_values]
        else:
            self.name, self.color_values = registry.resolve(name, default)

        self.scales: list = []

    @property
    def n_colors(self) -> int:
        """
        Get the number of colors in this palette
        :return: Number of colors in the palette
        """
        if self.color_values is None:
            return -1
        return len(self.color_values)

    @property
    def hex_colors(self) -> list[str]:
        """
        Get this palette's colors as hex codes
        :return: One hex code per color, empty if the palette has no colors
        """
        if self.color_values is None:
            return []
        return [convert.int_to_hex(rgb) for rgb in self.color_values]

    @property
    def yaml_hex(self) -> str:
        """
        Get the YAML representation of this palette
        :return: YAML string
        """
        if self.color_values is None:
            return ''
        return self.np_to_yaml(self.name, self.color_values, 'hex')

    @property
    def yaml_int(self) -> str:
        """
        Get the YAML representation of this palette
        :return: YAML string
        """
        if self.color_values is None:
            return ''
        return self.np_to_yaml(self.name, self.color_values, 'int')

    @property
    def yaml_float(self) -> str:
        """
        Get the YAML representation of this palette
        :return: YAML string
        """
        if self.color_values is None:
            return ''
        return self.np_to_yaml(self.name, self.color_values, 'float')

    @staticmethod
    def get_palette_values(name: str, default: str | None = None) -> list[list[int]] | None:
        """
        Get the color palette as a list of RGB triples
        :param name: Look for a palette with this name
        :param default: Return a palette with this name instead if the requested palette is not found
        :return: None if the palette name is not found, otherwise a list of RGB values
        """
        return registry.resolve(name, default)[1]

    @staticmethod
    def int_to_hex(rgb: list[int]) -> str:
        """
        Convert integer RGB values to a hex code
        :param rgb: List of exactly three integers with values 0-255 inclusive
        :return: The corresponding hex code starting with the '#' character
        """
        return convert.int_to_hex(rgb)

    @staticmethod
    def int_to_int(rgb: list[int]) -> list[int]:
        """
        Actually a no-op
        :param rgb: List of exactly three integers with values 0-255 inclusive
        :return: A list of exactly three integers with values from 0-255 inclusive
        """
        return convert.int_to_int(rgb)

    @staticmethod
    def int_to_float(rgb: list[int]) -> list[float]:
        """
        Convert integer RGB values to float RGB values
        :param rgb: List of exactly three integers with values 0-255 inclusive
        :return: A list of exactly three floats with values from 0-1 inclusive
        """
        return convert.int_to_float(rgb)

    @staticmethod
    def float_to_hex(rgb: list[float]) -> str:
        """
        Convert float RGB values to a hex code
        :param rgb: List of exactly three floats with values 0-1 inclusive
        :return: The corresponding hex code starting with the '#' character
        """
        return convert.float_to_hex(rgb)

    @staticmethod
    def hex_to_int(hex_code: str) -> list[int]:
        """
        Convert a color hex code to RGB integers
        :param hex_code: The hex code starting with the '#' character
        :return: A list of exactly three integers with values from 0-255 inclusive
        """
        return convert.hex_to_int(hex_code)

    @staticmethod
    def hex_to_float(hex_code: str) -> list[float]:
        """
        Convert a color hex code to RGB floats
        :param hex_code: The hex code starting with the '#' character
        :return: A list of exactly three floats with values from 0-1 inclusive
        """
        return convert.hex_to_float(hex_code)

    @staticmethod
    def np_to_yaml(name: str, values: list[list[int]], color_format: str = 'hex') -> str:
        """
        Convert palette values to YAML format
        :param name: Palette name (reflected in returned YAML)
        :param values: An array of RGB integer triples
        :param color_format: Value format: hex, int, float
        :return: YAML string representing the palette
        """
        # yaml is only needed to emit a palette, so keep the import out of the module load
        import yaml

        # get a format converter
        convert_color = convert.int_to_hex
        if color_format == 'int':
            convert_color = convert.int_to_int
        elif color_format == 'float':
            convert_color = convert.int_to_float

        yml: dict[str, list] = {name: [convert_color(rgb) for rgb in values]}
        return yaml.dump(yml, indent=2)

    def interpolate(self, n_colors: int, *, name: str | None = None) -> 'Palette':
        """
        Interpolates a colormap to a specified number of colors
        :param n_colors: The number of colors to interpolate to.
        :param name: Name for the new palette, defaulting to this palette's name
        :return: A Palette with interpolated colors
        """
        # create linear gradients of the original color and interpolated color
        colors = linspace(0, 1, len(self.color_values))
        colors_interp = linspace(0, 1, n_colors)

        # interpolate each channel
        r = interp(colors_interp, colors, [rgb[0] for rgb in self.color_values])
        g = interp(colors_interp, colors, [rgb[1] for rgb in self.color_values])
        b = interp(colors_interp, colors, [rgb[2] for rgb in self.color_values])

        # stack back into (n_colors, 3) with uint8 conversion, keeping the name we came from
        return Palette(name=name if name is not None else self.name,
                       color_values=stack([r, g, b], axis=1))

    def colormap(self, vmin: float, vmax: float) -> 'ColorMap':
        """
        Get a ColorMap that maps a value range onto this palette
        :param vmin: Low end of the value range
        :param vmax: High end of the value range
        :return: A ColorMap using this palette
        """
        from .colormap import ColorMap
        return ColorMap(self, vmin, vmax)

    def get_legend_graphic(self, full_width: int | None = None, full_height: int | None = None) -> bytes:
        """
        Generates a legend graphic for a specified colormap. Note this is currently a
        horizontal gradient of the colormap, not a legend with labels
        :param full_width: Width of the legend image in pixels
        :param full_height: Height of the legend image in pixels
        :return: Bytes containing the PNG image of the legend
        :raises ModuleNotFoundError: If the optional legend extra is not installed
        """
        from .legend import render_legend
        return render_legend(self, full_width, full_height, scales=self.scales)


# names that used to live in this module, kept resolvable for callers that import them from here
_MOVED: dict[str, str] = {
    'Scale': 'colors.scale',
    'ColorMap': 'colors.colormap',
    'linspace': 'colors.interp',
    'interp': 'colors.interp',
    'stack': 'colors.interp',
}


def __getattr__(name: str) -> object:
    """
    Resolve names that moved out of this module during the 2.0 re-organization
    :param name: Attribute being looked up
    :return: The requested object from its new home
    :raises AttributeError: If the name was never part of this module
    """
    target: str | None = _MOVED.get(name)
    if target is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')

    import importlib
    value = getattr(importlib.import_module(target), name)

    # cache the lookup so repeated access costs nothing
    globals()[name] = value
    return value
