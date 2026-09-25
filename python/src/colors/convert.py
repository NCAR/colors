"""
Color format conversions between hex codes, integer RGB, and float RGB.
Pure functions only -- this module has no dependencies outside the standard library.
"""


def hex_to_int(hex_code: str) -> list[int]:
    """
    Convert a color hex code to RGB integers
    :param hex_code: The hex code, with or without a leading '#', as RGB, ARGB, RRGGBB, or AARRGGBB
    :return: A list of exactly three integers with values from 0-255 inclusive
    :raises ValueError: If the hex code is not 3, 4, 6, or 8 digits long
    """
    return hex_to_rgba(hex_code)[:3]


def hex_to_rgba(hex_code: str) -> list[int]:
    """
    Convert a color hex code to RGB integers plus an alpha channel
    :param hex_code: The hex code, with or without a leading '#', as RGB, ARGB, RRGGBB, or AARRGGBB
    :return: A list of exactly four integers with values from 0-255 inclusive, alpha last
    :raises ValueError: If the hex code is not 3, 4, 6, or 8 digits long
    """
    # remove any leading '#' so we can work on digits alone
    digits: str = hex_code.lstrip('#')

    # expand the shorthand forms by doubling each digit, alpha leads in the 4 digit form
    if len(digits) == 3:
        digits = ''.join(d * 2 for d in digits)
    elif len(digits) == 4:
        digits = ''.join(d * 2 for d in digits)

    # the 8 digit form is AARRGGBB, so the alpha is in front of the color we want
    if len(digits) == 8:
        a = int(digits[0:2], 16)
        r = int(digits[2:4], 16)
        g = int(digits[4:6], 16)
        b = int(digits[6:8], 16)
        return [r, g, b, a]

    # anything else has to be the plain RRGGBB form
    if len(digits) != 6:
        raise ValueError(f'Unsupported hex code length: {hex_code!r}')

    # convert hex string to three integers, fully opaque
    r = int(digits[0:2], 16)
    g = int(digits[2:4], 16)
    b = int(digits[4:6], 16)
    return [r, g, b, 255]


def hex_to_float(hex_code: str) -> list[float]:
    """
    Convert a color hex code to RGB floats
    :param hex_code: The hex code, with or without a leading '#', as RGB, ARGB, RRGGBB, or AARRGGBB
    :return: A list of exactly three floats with values from 0-1 inclusive
    :raises ValueError: If the hex code is not 3, 4, 6, or 8 digits long
    """
    return int_to_float(hex_to_int(hex_code))


def int_to_hex(rgb: list[int]) -> str:
    """
    Convert integer RGB values to a hex code
    :param rgb: List of exactly three integers with values 0-255 inclusive
    :return: The corresponding hex code starting with the '#' character
    """
    r, g, b = rgb[:3]
    return f'#{r:02x}{g:02x}{b:02x}'


def int_to_int(rgb: list[int]) -> list[int]:
    """
    Actually a no-op
    :param rgb: List of exactly three integers with values 0-255 inclusive
    :return: A list of exactly three integers with values from 0-255 inclusive
    """
    return [int(rgb[i]) for i in range(3)]


def int_to_float(rgb: list[int]) -> list[float]:
    """
    Convert integer RGB values to float RGB values
    :param rgb: List of exactly three integers with values 0-255 inclusive
    :return: A list of exactly three floats with values from 0-1 inclusive
    """
    return [float(rgb[i] / 255.0) for i in range(3)]


def float_to_hex(rgb: list[float]) -> str:
    """
    Convert float RGB values to a hex code
    :param rgb: List of exactly three floats with values 0-1 inclusive
    :return: The corresponding hex code starting with the '#' character
    """
    r, g, b = rgb[:3]

    # clamp values to 0-1 range and scale to 0-255
    r_int: int = min(max(int(round(r * 255)), 0), 255)
    g_int: int = min(max(int(round(g * 255)), 0), 255)
    b_int: int = min(max(int(round(b * 255)), 0), 255)
    return int_to_hex([r_int, g_int, b_int])


def coerce_color(value: str | list[int] | tuple[int, ...] | None) -> list[int] | None:
    """
    Accept a color as either a hex code or a sequence of integers and normalize it
    :param value: A '#' prefixed hex code, a sequence of RGB or RGBA integers, or None
    :return: A list of integers, or None if no color was given
    """
    # nothing to coerce
    if value is None:
        return None

    # a hex code needs parsing, anything else is already a sequence of channel values
    if isinstance(value, str):
        return hex_to_int(value)
    return [int(channel) for channel in value]


def format_color(rgb: list[int], color_format: str = 'hex') -> str | list[int] | list[float]:
    """
    Convert integer RGB values into one of the supported output formats
    :param rgb: List of exactly three integers with values 0-255 inclusive
    :param color_format: Format to return, can be 'hex', 'int', or 'float'
    :return: Color value in the requested format
    :raises ValueError: If the color format is invalid
    """
    if color_format == 'hex':
        return int_to_hex(rgb)
    if color_format == 'int':
        return int_to_int(rgb)
    if color_format == 'float':
        return int_to_float(rgb)
    raise ValueError('Invalid color format')
