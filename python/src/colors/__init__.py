"""
Color palettes, value-to-color mapping, and legend graphics.
Everything exported eagerly here works with no dependencies beyond pyyaml; the legend renderer
is resolved on first use so that Pillow, an optional extra, stays out of the import graph.
"""
import importlib
from typing import TYPE_CHECKING

from .colormap import ColorMap, color_at
from .palette import Palette
from .registry import PALETTES, palette_names
from .scale import Scale

# declare the lazily resolved names for linters and type checkers. this block never runs, so
# Pillow stays out of the import graph -- see __getattr__ below for the actual resolution
if TYPE_CHECKING:
    from .legend import Legend, ScaleRenderer, render_legend


__all__ = ['ColorMap', 'Legend', 'PALETTES', 'Palette', 'Scale', 'ScaleRenderer',
           'color_at', 'palette_names', 'render_legend', '__version__']


# names that need Pillow, resolved by __getattr__ only when a caller actually asks for them
_LAZY: dict[str, str] = {
    'Legend': 'colors.legend',
    'ScaleRenderer': 'colors.legend',
    'render_legend': 'colors.legend',
}


def _get_version() -> str:
    """
    Get the installed version of this package
    :return: The version string, or 'unknown' if the package metadata is unavailable
    """
    from importlib.metadata import PackageNotFoundError, version
    try:
        return version('colors')
    except PackageNotFoundError:
        return 'unknown'


__version__: str = _get_version()


def __getattr__(name: str) -> object:
    """
    Resolve the legend rendering names on first access
    :param name: Attribute being looked up
    :return: The requested object from the legend module
    :raises AttributeError: If the name is not part of this package's public surface
    :raises ModuleNotFoundError: If the optional legend extra is not installed
    """
    target: str | None = _LAZY.get(name)
    if target is None:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')

    value = getattr(importlib.import_module(target), name)

    # cache the lookup so repeated access does not go through the import machinery again
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    """
    List this package's public names
    :return: The sorted contents of __all__
    """
    return sorted(__all__)
