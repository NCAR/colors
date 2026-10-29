"""
Test the convert functions
"""


from colors.convert import *


def test_convert_color() -> None:
    """
    Test the functions to convert a color
    """
    hex_code: str = '#88AFDE90'
    float_code: list[float] = [0.6862745098039216, 0.8705882352941177, 0.5647058823529412]
    int_code: list[int] = [175, 222, 144, 136]

    assert int_code == hex_to_rgba(hex_code)
    assert int_code[:-1] == hex_to_int(hex_code)
    assert float_code == hex_to_float(hex_code)

    float_vals: list[float] = [0.3, 0.4, 0.7]
    assert '#4c66b2' == float_to_hex(float_vals)

    assert '#AFDE90' == format_color(int_code, 'hex').upper()
    assert float_code == format_color(int_code, 'float')
