# colors

Color palettes, value-to-color mapping, and legend graphics.

The package is organized around three separate ideas, so you only pay for the one you need:

| You want to                        | Use                            | Needs Pillow |
|------------------------------------|--------------------------------|--------------|
| Map a number to a color            | `colors.ColorMap`              | no           |
| Work with a palette's colors       | `colors.Palette`               | no           |
| Describe how a legend should look  | `colors.Scale`                 | no           |
| Draw a legend graphic              | `colors.legend`                | yes          |

Pillow is an optional extra. Importing `colors` and mapping values to colors works with nothing
but `pyyaml` installed, which keeps serverless deployments free of native shared libraries.
Palette definitions are read from the packaged resource on first use, not at import time.

## How To Install

```bash
pip install --upgrade colors                # palettes and color mapping (depends only on pyyaml)
pip install --upgrade 'colors[legend]'      # also installs Pillow for legend graphics, colors-legend and colors-swatches
```

Confirm it worked:

```bash
colors-hex --version
colors-hex -p viridis -n 4
```

## How To Build

The project metadata lives in `src/pyproject.toml`, so builds run from the `src` directory.

```bash
cd src
python -m pip install build
python -m build
```

That writes a wheel and a source distribution to `src/dist`:

```
dist/colors-2.0.0-py3-none-any.whl
dist/colors-2.0.0.tar.gz
```

Install the result, with or without legend rendering:

```bash
pip install dist/colors-2.0.0-py3-none-any.whl              # core only, pulls pyyaml
pip install 'dist/colors-2.0.0-py3-none-any.whl[legend]'    # adds pillow
```

For development, an editable install from the same directory:

```bash
cd src
pip install -e '.[legend]'
```

Requires Python 3.11 or newer. The legend extra asks for `pillow>=11.1,<13` rather than a single
pinned version, because older Pillow releases have no wheels for the newest Python versions and
fall back to building from source.

## How To Use As Library

### Map a value to a color

This is the common case and needs nothing but a palette name and a value range.

```python
from colors import ColorMap

cmap = ColorMap('x-Sst', 0.0, 32.0)
cmap.map_color(21.5)            # '#eb9b00'
cmap.map_color(21.5, 'int')     # [235, 155, 0]
cmap.map_color(21.5, 'float')   # [0.9215686274509803, 0.6078431372549019, 0.0]
```

Values outside the range clamp to the end colors. `ColorMap` also accepts a `Palette` object or a
raw list of RGB triples in place of the name:

```python
from colors import ColorMap, Palette

ColorMap(Palette('viridis'), 0, 100).map_color(50)
ColorMap([[0, 0, 0], [255, 255, 255]], 0, 1).map_color(1)      # '#ffffff'
```

Mapping many values, such as every pixel of a map tile:

```python
tile = [cmap.map_color(v) for v in values]
```

For a single lookup where keeping a `ColorMap` around is not worth it:

```python
import colors

colors.color_at('div-RdBu', 12.3, vmin=-5, vmax=40)     # '#fddbc7'
```

Useful attributes: `cmap.vmin`, `cmap.vmax`, `cmap.palette`, `cmap.n_colors`, and
`cmap.index(x)` if you want the palette index rather than the color.

### Choosing the number of colors

A `ColorMap` indexes straight into its palette, so the number of discrete color bands is the
number of colors in the palette. Resample a palette when a request asks for a specific count:

```python
from colors import ColorMap, Palette

palette = Palette('x-Sst').interpolate(256)
cmap = ColorMap(palette, 0.0, 32.0)
cmap.n_colors                    # 256
```

`interpolate` returns a new `Palette` and keeps the original name, so it is safe to chain.

### Working with palettes

```python
from colors import Palette
import colors

p = Palette('viridis')
p.n_colors                       # 25 -- palettes vary in how many colors they define
p.color_values[:2]               # [[68, 1, 84], [71, 15, 98]]
p.hex_colors[:2]                 # ['#440154', '#470f62']
p.yaml_hex                       # 'viridis:\n- \'#440154\'\n...'

colors.palette_names()           # ['BrBG', 'alg', ... ] 98 names
colors.palette_names(True)       # each name also paired with its '-inv' form
len(colors.PALETTES)             # 98
'viridis' in colors.PALETTES     # True
```

Append `-inv` to any palette name to get it reversed:

```python
Palette('viridis-inv').color_values[0]      # [230, 232, 8]
```

Palette names are matched case-insensitively, and a fallback palette can be supplied for when a
name is not found:

```python
Palette('VIRIDIS')                          # same colors as 'viridis'
Palette('no-such-palette', 'viridis')       # falls back to viridis
```

Note that `BrBG` and `brbg` are two different palettes that differ only in case. An exact name
match always wins, so ask for the one you want by its exact name.

Color format conversions are available as module functions, and also as static methods on
`Palette` for backwards compatibility:

```python
from colors import convert

convert.hex_to_int('#440154')        # [68, 1, 84]
convert.hex_to_rgba('#ff543005')     # [84, 48, 5, 255]  -- 8 digit codes are AARRGGBB
convert.int_to_hex([68, 1, 84])      # '#440154'
convert.int_to_float([68, 1, 84])    # [0.266..., 0.003..., 0.329...]
convert.float_to_hex([0.0, 0.5, 1.0])  # '#0080ff'
```

### Drawing a legend graphic

Legend rendering needs the `legend` extra. The easiest path states the value range once, on the
`ColorMap` that already owns it:

```python
from colors import ColorMap

png: bytes = ColorMap('x-Sst', 0.0, 32.0).legend(
    width=425, height=80, label='Sea Surface Temp (C)', ticks=5,
)
```

Any `Scale` attribute can be passed as a keyword: `label`, `ticks`, `position` (`'top'` or
`'bottom'`), `precision`, `font_family`, `font_size`, `color`, `background_color`, `padding`,
`margin`.

For more control, build the configuration yourself. `Scale` is plain configuration and imports no
image library, so it can be built from request parameters even where Pillow is unavailable:

```python
from colors import Palette, Scale
from colors.legend import render_legend

scale = Scale(label='SST (C)', position='bottom', ticks=5, precision=1, min=0, max=32)
png = render_legend(Palette('x-Sst').interpolate(256), 425, 80, scales=[scale])
```

A `Scale` also accepts a dictionary, which is handy when the values arrive as JSON:

```python
scale = Scale({'label': 'SST (C)', 'ticks': 5, 'min': 0, 'max': 32})
```

The `Legend` class is available when you want the image rather than the encoded bytes:

```python
from colors import Palette
from colors.legend import Legend

image = Legend(Palette('viridis').interpolate(64), scales=[scale]).to_image(425, 80)
png = Legend(Palette('viridis').interpolate(64)).to_png(425, 80)
```

A palette can also render itself, with any scales attached to it:

```python
p = Palette('x-Sst').interpolate(64)
p.scales.append(Scale(label='SST', min=0, max=32, ticks=5))
png = p.get_legend_graphic(425, 80)
```

Without the extra installed, every one of these raises `ModuleNotFoundError` explaining how to
fix it. To check up front:

```python
from colors.legend import require_pillow       # raises if Pillow is unavailable
```

## How To Use CLI

Three commands are installed with the package. Every one accepts `-v` / `--version`, and
`colors-hex` is the only one that works without the `legend` extra.

### colors-hex

Print a palette's colors as a comma-separated list.

```
-p, --palette      Name of the palette (required)
-n, --num-colors   Number of colors to return from the palette (default: 4)
-f, --format       Color value format: hex, int, or float (default: hex)
```

```bash
$ colors-hex -p div-RdBu -n 8
#67001f, #c1373a, #f09b7a, #fbe3d5, #dceaf2, #87beda, #3079b6, #053061

$ colors-hex -p viridis -n 2 -f int
[68, 1, 84], [230, 232, 8]

$ colors-hex -p viridis-inv -n 3
#e6e808, #2993af, #440154
```

### colors-legend

Write a legend graphic to a PNG file. Requires the `legend` extra.

```
-p, --palette      Name of the palette (required)
-o, --out          Output file name (required)
-n, --num-colors   Number of colors to return from the palette (default: 4)
-x, --width        Width of the legend graphic (default: 425)
-y, --height       Height of the legend graphic (default: 80)
-l, --label        Label to draw on the scale
-t, --ticks        Number of tick marks to draw on the scale
    --vmin         Low end of the value range the palette covers
    --vmax         High end of the value range the palette covers
    --position     Where to draw the scale: top or bottom
```

A plain gradient with no labels:

```bash
colors-legend -p x-Sst -n 64 -o legend.png -x 425 -y 80
```

A labelled scale with tick marks. Give both `--vmin` and `--vmax` so the ticks can be labelled
with real values:

```bash
colors-legend -p x-Sst -n 64 -o legend.png -x 425 -y 80 \
    --label 'Sea Surface Temp (C)' --ticks 5 --vmin 0 --vmax 32
```

The same thing with the scale above the gradient:

```bash
colors-legend -p div-RdBu -n 32 -o anomaly.png --label 'Anomaly' \
    --ticks 3 --vmin -5 --vmax 5 --position top
```

### colors-swatches

Write an HTML page showing every palette, one gradient per palette. Requires the `legend` extra.

```
-f, --file         Name of the output html file (default: ./swatches.html)
-n, --num-colors   Number of discrete colors in the palette (default: 512)
-i, --inverted     Show the inverted palette
```

```bash
$ colors-swatches -f swatches.html -n 512
Here you go...swatches.html

$ colors-swatches -f inverted.html -i
Here you go...inverted.html
```
