"""
Declarative configuration for a legend scale band.
This is the half of a scale that describes what it should look like, with none of the drawing,
so it can be built from request parameters in an environment where Pillow is not installed.
"""
from . import convert

# every attribute a caller may set, and the only keys read from a data dictionary
KEYS: tuple[str, ...] = ('label', 'position', 'font_family', 'font_size', 'color',
                         'background_color', 'padding', 'margin', 'min', 'max',
                         'ticks', 'precision')

# where a scale may be drawn, and the aliases accepted for each
POSITIONS: dict[str, str] = {'bottom': 'bottom', 'lower': 'bottom', 'top': 'top', 'upper': 'top'}


class Scale:
    """
    Appearance of one legend scale band: its label, typography, spacing, and tick marks.
    Contains no rendering code -- see colors.legend.ScaleRenderer for that.
    """
    # kept as a list, and derived from KEYS, so the two can never drift apart
    ALL_KEYS: list[str] = list(KEYS)

    def __init__(self, data: dict | None = None, **kwargs):
        """
        Default constructor
        :param data: Initial values for this object, keyed by any of ALL_KEYS
        :param kwargs: Initial values given as keyword arguments, taking precedence over data
        """
        # accept a dictionary, keyword arguments, or neither
        values: dict = dict(data or {})
        values.update(kwargs)

        # set the attribute defaults
        self.label: str | None = values.get('label', None)
        self.position: str = self._coerce_position(values.get('position', 'bottom'))
        self.font_family: str = values.get('font_family', 'Arial')
        self.font_size: int = values.get('font_size', 12)
        self.color: list[int] | None = convert.coerce_color(values.get('color', [0, 0, 0]))
        self.background_color: list[int] | None = convert.coerce_color(values.get('background_color', None))
        self.padding: list[int] = list(values.get('padding', [10, 10, 10, 10]))  # follows CSS: top, right, bottom, left
        self.margin: list[int] = list(values.get('margin', [0, 0, 0, 0]))  # follows CSS: top, right, bottom, left
        self.min: float | None = values.get('min', None)
        self.max: float | None = values.get('max', None)
        self.ticks: int | None = values.get('ticks', None)
        self.precision: int = values.get('precision', 1)

    @classmethod
    def from_dict(cls, data: dict | None = None) -> 'Scale':
        """
        Build a Scale from a dictionary of attribute values
        :param data: Initial values for this object, keyed by any of ALL_KEYS
        :return: The new Scale
        """
        return cls(data)

    def to_dict(self) -> dict:
        """
        Get this scale's attributes as a dictionary
        :return: A dictionary keyed by every name in ALL_KEYS
        """
        return {key: getattr(self, key) for key in KEYS}

    @staticmethod
    def _coerce_position(position: str | None) -> str:
        """
        Normalize a position value onto one of the positions the renderer understands
        :param position: Requested position, which may be an alias such as 'lower'
        :return: Either 'top' or 'bottom'
        """
        if position is None:
            return 'bottom'
        return POSITIONS.get(str(position).lower(), 'bottom')

    def tick_values(self) -> list[float]:
        """
        Get the values the tick labels should show
        :return: One value per tick, evenly spaced across the value range, empty if unavailable
        """
        # nothing to label without both a range and a tick count
        if self.min is None or self.max is None or not self.ticks:
            return []

        # a single tick sits at the low end of the range
        if self.ticks == 1:
            return [float(self.min)]

        span: float = self.max - self.min
        return [self.min + i * span / (self.ticks - 1) for i in range(self.ticks)]

    def draw_scale(self, image, draw=None) -> None:
        """
        Draw this scale on an image
        :param image: The image to draw on
        :param draw: Unused, the renderer creates its own drawing context
        :raises ModuleNotFoundError: If the optional legend extra is not installed
        """
        from .legend import ScaleRenderer
        ScaleRenderer(self).draw(image)

    @property
    def font_dir(self) -> str:
        """
        Get the font directory from this package
        :return: Path to the directory holding the packaged fonts
        """
        from .legend import font_dir
        return font_dir()

    @property
    def font(self):
        """
        Get the font to use for this scale
        :return: Font definition
        :raises ModuleNotFoundError: If the optional legend extra is not installed
        """
        from .legend import resolve_font
        return resolve_font(self.font_family, self.font_size)

    @property
    def smaller_font(self):
        """
        Get a smaller font
        :return: Font definition
        :raises ModuleNotFoundError: If the optional legend extra is not installed
        """
        from .legend import resolve_font
        return resolve_font(self.font_family, self.font_size * 0.7)
