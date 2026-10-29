"""
Test the Palette class
"""

import yaml
from hashlib import sha256
from base64 import b64encode
from colors import Palette


def test_palette_interpolate() -> None:
    """
    Test the Palette's interpolate functions
    """
    # expected number of palettes available
    assert 98 == len(Palette.PALETTES)

    # constants
    palette_name: str = 'autumn-inv'
    int_40: list[int] = [255, 232, 0]
    hex_31: str = '#f3ff00'
    hex_90: str = '#ff2300'
    yaml_hex_sha256: str = 'QgsurJaZO0l0JHJrGgTLsXwQEOi6eOxiSWadsNqcxb4='
    yaml_int_sha256: str = 'zArPLX2Ynewy7npDBEEZ/TkCt2kjj1lb03AJA+s58D0='
    yaml_float_sha256: str = 'KaL7Mke4XK2uuhv3u8KUzLj/x+Jp75XbcObAS5eGETY='

    # create a sample palette
    p = Palette(palette_name).interpolate(100)

    # check number of colors
    assert 100 == len(p.color_values) == p.n_colors

    # test interpolate and check color values
    assert int_40 == p.color_values[40]
    assert hex_31 == p.int_to_hex(p.color_values[31])
    assert hex_90 == p.hex_colors[90]

    # check the hex YAML output
    yaml_hex: str = p.yaml_hex
    hex_dict: dict = yaml.safe_load(yaml_hex)
    assert palette_name in hex_dict
    yaml_hex_chksum = b64encode(sha256(yaml_hex.encode()).digest()).decode()
    assert yaml_hex_sha256 == yaml_hex_chksum

    # check the int YAML output
    yaml_int: str = p.yaml_int
    int_dict: dict = yaml.safe_load(yaml_int)
    assert palette_name in int_dict
    yaml_int_chksum = b64encode(sha256(yaml_int.encode()).digest()).decode()
    assert yaml_int_sha256 == yaml_int_chksum

    # check the float YAML output
    yaml_float: str = p.yaml_float
    float_dict: dict = yaml.safe_load(yaml_float)
    assert palette_name in float_dict
    yaml_float_chksum = b64encode(sha256(yaml_float.encode()).digest()).decode()
    assert yaml_float_sha256 == yaml_float_chksum
