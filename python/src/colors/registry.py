"""
Palette definition loading and lookup.
Definitions are read from the packaged resource on first use, not at import time, so that
importing this package costs nothing until a palette is actually asked for.
"""
import logging
import pkgutil
import warnings
from collections.abc import Iterator, Mapping

from . import convert

# the resource holding the palette definitions
RESOURCE: str = 'resources/palettes.yaml'

# suffix a caller appends to a palette name to ask for the reversed palette
INVERTED_SUFFIX: str = '-inv'

log = logging.getLogger('colors')

# the palette definitions, loaded lazily by load_definitions
_definitions: dict[str, list[str]] | None = None


def load_definitions() -> dict[str, list[str]]:
    """
    Load the palette definitions from the packaged resource file, caching the result
    :return: A map of canonical palette names to a list of palette colors as hex codes
    """
    global _definitions

    # return the cached definitions if we already loaded them
    if _definitions is not None:
        return _definitions

    # yaml is only needed here, so keep the import local to the one function that reads a file
    try:
        import yaml
        _definitions = yaml.safe_load(pkgutil.get_data('colors', RESOURCE))
    except Exception as e:
        log.error('colors.registry: Failed to load color palette definitions')
        log.error(e)
        _definitions = {}

    return _definitions


def is_loaded() -> bool:
    """
    Check whether the palette definitions have been read from disk yet
    :return: True if the definitions are loaded and cached
    """
    return _definitions is not None


def reload() -> None:
    """
    Drop the cached palette definitions so the next lookup reads the resource again
    """
    global _definitions
    _definitions = None


def canonical(name: str) -> str | None:
    """
    Find the definition key matching a palette name, ignoring case
    :param name: Look for a palette with this name
    :return: The canonical palette name, or None if there is no such palette
    """
    # nothing to look up
    if name is None:
        return None

    definitions: dict[str, list[str]] = load_definitions()

    # an exact match always wins
    if name in definitions:
        return name

    # otherwise take the first definition that matches ignoring case. note that 'BrBG' and 'brbg'
    # are two different palettes, so a mixed-case request can only resolve to one of them
    folded: str = name.lower()
    for key in definitions:
        if key.lower() == folded:
            return key
    return None


def palette_names(include_inverted: bool = False) -> list[str]:
    """
    Get the names of every available palette
    :param include_inverted: Also include the '-inv' name of each palette
    :return: A list of canonical palette names
    """
    names: list[str] = list(load_definitions().keys())

    # optionally pair every palette with its inverted form
    if include_inverted:
        return [n for name in names for n in (name, f'{name}{INVERTED_SUFFIX}')]
    return names


def resolve(name: str | None, default: str | None = None) -> tuple[str | None, list[list[int]] | None]:
    """
    Look up a palette by name and convert its colors to RGB integers
    :param name: Look for a palette with this name, optionally with the '-inv' suffix
    :param default: Return a palette with this name instead if the requested palette is not found
    :return: The resolved palette name and its RGB values, or (None, None) if nothing was found
    """
    # maybe create an empty palette
    if name is None and default is None:
        return None, None

    # use the default if no name is given
    if name is None:
        return resolve(default)

    # check for an inverted palette
    do_inversion: bool = name.endswith(INVERTED_SUFFIX)
    lookup: str = name[:-len(INVERTED_SUFFIX)] if do_inversion else name

    # try to return the requested palette, ignoring case as the old lookup did
    key: str | None = canonical(lookup)
    if key is not None:
        # build and return the requested palette
        rgb_ints: list[list[int]] = [convert.hex_to_int(color) for color in load_definitions()[key]]
        if do_inversion:
            rgb_ints = rgb_ints[::-1]
        return name, rgb_ints

    # be helpful and fall back to the default palette
    if default is not None:
        return resolve(default)

    # sorry, that is not a valid palette name
    log.warning('WARN: Invalid palette name: %s', name)
    return None, None


class PaletteRegistry(Mapping):
    """
    Case-insensitive, lazily loaded mapping of palette name to its list of hex color codes.
    Iteration yields canonical names only, so a caller walking the registry sees each palette once.
    """

    def __getitem__(self, name: str) -> list[str]:
        """
        Get the hex color codes of a palette, ignoring case
        :param name: Look for a palette with this name
        :return: The list of hex color codes defining the palette
        :raises KeyError: If there is no palette with that name
        """
        key: str | None = canonical(name)
        if key is None:
            raise KeyError(name)
        return load_definitions()[key]

    def __iter__(self) -> Iterator[str]:
        """
        Iterate the canonical palette names
        :return: An iterator over canonical palette names
        """
        return iter(load_definitions())

    def __len__(self) -> int:
        """
        Count the available palettes
        :return: The number of palettes, counting each one once
        """
        return len(load_definitions())

    def __contains__(self, name: object) -> bool:
        """
        Check whether a palette exists, ignoring case
        :param name: Look for a palette with this name
        :return: True if a palette with that name is defined
        """
        return isinstance(name, str) and canonical(name) is not None

    def canonical(self, name: str) -> str | None:
        """
        Find the definition key matching a palette name, ignoring case
        :param name: Look for a palette with this name
        :return: The canonical palette name, or None if there is no such palette
        """
        return canonical(name)

    def reload(self) -> None:
        """
        Drop the cached palette definitions so the next lookup reads the resource again
        """
        reload()


# the shared registry every Palette consults
PALETTES: PaletteRegistry = PaletteRegistry()


def inject_palettes(cls: type) -> type:
    """
    Point a class at the shared palette registry
    :param cls: The class being decorated
    :return: The decorated class, with its PALETTES attribute set to the shared registry
    :deprecated: Palette definitions now load on demand, so nothing needs injecting
    """
    warnings.warn('colors.inject_palettes is deprecated; palette definitions now load on demand',
                  DeprecationWarning, stacklevel=2)
    cls.PALETTES = PALETTES
    return cls
