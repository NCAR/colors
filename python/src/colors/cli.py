import argparse
import base64
import sys
from . import ColorMap, Palette, Scale, palette_names


def cli_legend():
    """
    Render a color legend graphic
    """
    # maybe print the version
    if _check_version():
        return

    # parse the command line parameters
    parser = argparse.ArgumentParser(
        description='Color legend graphic generator',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-p', '--palette', help='Name of the palette', type=str, required=True)
    parser.add_argument('-n', '--num-colors', help='Number of colors to return from the palette', type=int, required=False, default=4)
    parser.add_argument('-o', '--out', help='Output file name', type=str, required=True)
    parser.add_argument('-x', '--width', help='Width of the legend graphic', type=int, required=False, default=425)
    parser.add_argument('-y', '--height', help='Height of the legend graphic', type=int, required=False, default=80)
    parser.add_argument('-l', '--label', help='Label to draw on the scale', type=str, required=False)
    parser.add_argument('-t', '--ticks', help='Number of tick marks to draw on the scale', type=int, required=False)
    parser.add_argument('--vmin', help='Low end of the value range the palette covers', type=float, required=False)
    parser.add_argument('--vmax', help='High end of the value range the palette covers', type=float, required=False)
    parser.add_argument('--position', help='Where to draw the scale', type=str, required=False, choices=['top', 'bottom'])
    args = parser.parse_args()

    # create a palette object with the requested number of colors
    p = Palette(args.palette).interpolate(args.num_colors)

    # collect whichever scale attributes were asked for
    scale_kwargs: dict = {}
    if args.label is not None:
        scale_kwargs['label'] = args.label
    if args.ticks is not None:
        scale_kwargs['ticks'] = args.ticks
    if args.position is not None:
        scale_kwargs['position'] = args.position

    # create the image bytes, letting the ColorMap supply the value range when we have one
    if args.vmin is not None and args.vmax is not None:
        graphic: bytes = ColorMap(p, args.vmin, args.vmax).legend(args.width, args.height, **scale_kwargs)
    else:
        if scale_kwargs:
            p.scales.append(Scale(**scale_kwargs))
        graphic = p.get_legend_graphic(args.width, args.height)

    # save the image bytes
    with open(args.out, 'wb') as out:
        out.write(graphic)


def cli_hex_list_from_palette():
    """
    Get a comma-separated list of hex values from a palette
    """
    # maybe print the version
    if _check_version():
        return

    # parse the command line parameters
    parser = argparse.ArgumentParser(
        description='Hex code palette generator',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-p', '--palette', help='Name of the palette', type=str, required=True)
    parser.add_argument('-n', '--num-colors', help='Number of colors to return from the palette', type=int, required=False, default=4)
    parser.add_argument('-f', '--format', help='Color value format', type=str, required=False, default='hex', choices=['hex', 'int', 'float'])
    args = parser.parse_args()

    # get a list of colors from the palette
    colors = Palette(args.palette).interpolate(args.num_colors).color_values

    # convert colors to a list of values in the requested format
    from . import convert
    values: list[str] = [str(convert.format_color(c, args.format)) for c in colors]

    # print out the comma-separated list of values
    print(', '.join(values))


def cli_palette_swatches():
    """
    Create swatch files for each color palette
    """
    # maybe print the version
    if _check_version():
        return

    # parse the command line parameters
    parser = argparse.ArgumentParser(
        description='Swatch generator',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-f', '--file', help='Name of the output html file', type=str, required=False, default='./swatches.html')
    parser.add_argument('-n', '--num-colors', help='Number of discrete colors in the palette', type=int, required=False, default=512)
    parser.add_argument('-i', '--inverted', help='Show the inverted palette', action='store_true')
    args = parser.parse_args()

    # get the list of all palette names and inverted palettes
    names: list[str] = palette_names()
    modifiers: list[str] = ['' if not args.inverted else '-inv']

    # write a PNG swatch for each palette and palette modifier
    html: list[str] = ['<html><head><style>.palette{text-align:center; max-width: 100%; width:1000px;margin:10px auto 10px auto; font-size: 2rem; font-family: "avenir next"; height: 75px; align-content: center; text-transform: uppercase; font-weight: 700;}</style></head><body>']
    for name in names:
        for modifier in modifiers:
            p_name: str = f'{name}{modifier}'
            p: Palette = Palette(p_name).interpolate(n_colors=args.num_colors)
            img: bytes = p.get_legend_graphic(512, 40)
            b64: str = f'data:image/png;base64,' + base64.b64encode(img).decode()
            html.append(f'<div class="palette" style="background-image:url({b64}); background-position:center; background-size:cover; background-repeat:no-repeat;">{p_name}</div>')

    # write an index.html file to see the swatches easily in a browser
    html.append('</body></html>')
    with open(args.file, 'w') as swatches_html:
        swatches_html.writelines(html)

    # done
    print(f'Here you go...{args.file}')



def _check_version() -> bool:
    """
    Check if user wants to print a version and exit
    :return: True if user wants to print a version and exit
    """
    if '-v' in sys.argv or '--version' in sys.argv:
        _print_version()
        return True
    return False


def _print_version() -> None:
    """
    Print the current version of the colors package as declared in pyproject.toml.
    :return: None
    """
    from . import __version__
    print(f'colors v{__version__}')
