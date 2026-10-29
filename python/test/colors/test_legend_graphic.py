"""
Test the legend graphic functions
"""

from hashlib import sha256
from base64 import b64encode
from colors import Legend, Scale, Palette, ColorMap
from colors.convert import hex_to_int


def test_legend_graphic() -> None:
    """
    Create a legend graphic and check that it is the expected value
    """
    scale_config = {
        'label': 'My Variable Name (units)',
        'position': 'top',
        'font_family': 'arial',
        'font_size': 24,
        'color': hex_to_int('#404b4b'),
        'min': 2,
        'max': 5,
        'ticks': 7,
        'precision': 1 }
    l = Legend(Palette('autumn-inv').interpolate(6), [Scale(scale_config)])

    png_bytes: bytes = l.to_png(600, 200)
    assert 'Jm7j6lxWSmbuL8MnvthGrSP+THn07yE9C3vvkDA6fzo=' == b64encode(sha256(png_bytes).digest()).decode()


def test_color_map() -> None:
    """
    Test the color map functions
    """
    cmap = ColorMap(Palette('autumn-inv').interpolate(6), 2, 5)

    expected: list[str] = ['#78ff00', '#78ff00', '#c6ff00', '#ffea00', '#ffea00', '#ffea00', '#ff9c00', '#ff9c00', '#ff4e00', '#ff4e00', '#ff0000']
    for i in range(0, 11):
        value: float = (i/10 * 3) + 2
        assert expected[i] == cmap.map_color(value, 'hex')
