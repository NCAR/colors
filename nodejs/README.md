# @ncar/colors

Color palettes and value-to-color mapping for NodeJS, written in TypeScript. It is the sibling of the
Python `colors` package and shares its palette definitions, so both produce the same colors.

The package is organized around three ideas:

| You want to                        | Use                    |
|------------------------------------|------------------------|
| Map a number to a color            | `ColorMap`             |
| Work with a palette's colors       | `Palette`              |
| Describe a value range and display options | `Scale`        |

PNG legend rendering is not available in the NodeJS package; use the Python package for that. To draw a
color bar in a web page, see [Render a palette as a CSS gradient](#render-a-palette-as-a-css-gradient).

## How To Install

```bash
npm install @ncar/colors
```

Type declarations are included; no `@types` package is needed. Confirm the install worked:

```bash
npx --package @ncar/colors colors-hex-list -p viridis -n 4
```

## How To Build

```bash
cd nodejs
npm install
npm run build
```

This compiles `src` to `dist` and copies `src/resources` (the palette definitions) next to it.

## How To Use As Library

### Map a value to a color

A `ColorMap` combines a `Palette` with a `Scale` whose `min` and `max` give the value range. Values
outside the range clamp to the end colors.

```ts
import { ColorMap, Palette, Scale } from '@ncar/colors';

const cmap = new ColorMap(new Palette('x-Sst'), new Scale({ min: 0, max: 32 }));
cmap.mapColor(21.5);            // '#eb9b00'
cmap.mapColor(21.5, 'int');     // [235, 155, 0]
cmap.mapColor(21.5, 'float');   // [0.9215..., 0.6078..., 0]
```

`mapColor` throws if the palette is empty or the scale has no `min`/`max`.

### Choosing the number of colors

A `ColorMap` indexes straight into its palette, so the number of discrete color bands is the number
of colors in the palette. Resample a palette when you need a specific count:

```ts
const palette = new Palette('x-Sst').interpolate(256);
const cmap = new ColorMap(palette, new Scale({ min: 0, max: 32 }));
palette.nColors;                // 256
```

`interpolate` returns a new `Palette` and keeps the original name.

### Working with palettes

```ts
import { Palette } from '@ncar/colors';

const p = new Palette('viridis');
p.nColors;                      // palettes vary in how many colors they define
p.colorValues;                  // RGB triples, e.g. [[68, 1, 84], ...]
p.yamlHex;                      // YAML for the palette; also yamlInt and yamlFloat

Object.keys(Palette.PALETTES);  // every available palette name
```

Append `-inv` to any palette name to get it reversed, and pass a second argument as a fallback for
when the name is not found:

```ts
new Palette('viridis-inv').colorValues![0];     // [230, 232, 8]
new Palette('no-such-palette', 'viridis');      // falls back to viridis
```

Names are matched exactly, then in lower case, then in upper case.

Color format conversions and interpolation helpers are exported as functions:

```ts
import { hexToInt, intToHex, intToFloat, floatToHex, linspace, interp, stack } from '@ncar/colors';

hexToInt('#440154');            // [68, 1, 84]
intToHex([68, 1, 84]);          // '#440154'
intToFloat([68, 1, 84]);        // [0.266..., 0.003..., 0.329...]
floatToHex([0, 0.5, 1]);        // '#0080ff'
```

### Describing a scale

`Scale` is plain configuration. All options are optional:

```ts
import { Scale } from '@ncar/colors';

const scale = new Scale({
  label: 'Sea Surface Temp (C)',
  min: 0, max: 32,
  ticks: 5, precision: 1,
  position: 'lower',            // default
  fontFamily: 'Arial', fontSize: 12,
  color: '#000000',             // hex string or RGB triple
  backgroundColor: [255, 255, 255],
  padding: [10, 10, 10, 10],    // top, right, bottom, left (like CSS)
  margin: [0, 0, 0, 0],
});
```

### Render a palette as a CSS gradient

Turn a palette into a `linear-gradient(...)` and set it as an element's `background-image`. This
makes a color bar with no image files and no canvas:

```ts
import { Palette, intToHex } from '@ncar/colors';

/** Build a CSS linear-gradient() from a palette, resampled to `nColors` stops. */
function paletteGradient(name: string, nColors = 64, direction = 'to right'): string {
  const stops = new Palette(name).interpolate(nColors).colorValues!.map(intToHex);
  return `linear-gradient(${direction}, ${stops.join(', ')})`;
}

const bar = document.getElementById('legend-bar')!;
bar.style.backgroundImage = paletteGradient('x-Sst');
// linear-gradient(to right, #000099, ..., #990000)

// a vertical bar, with the high values at the top
bar.style.backgroundImage = paletteGradient('viridis', 64, 'to top');
```

```html
<div id="legend-bar" style="width: 425px; height: 24px;"></div>
```

Browsers blend smoothly between stops, so a handful of colors is enough for continuous data. For a
banded, discrete look, use the palette at its native size and repeat each stop
(e.g. `#440154 0% 10%, #470f62 10% 20%, ...`).

> **Note:** the library loads its palette file with Node's `fs`, so run this where that is available:
> server-side, in a build step, or through a bundler configured for it. A common pattern is to compute
> the gradient string on the server and send it to the page.

## How To Use CLI

One command is installed with the package. It accepts `-v` / `--version`.

### colors-hex-list

Print a palette's colors as a comma-separated list of hex codes.

```
-p, --palette      Name of the palette (required)
-n, --num-colors   Number of colors to return from the palette (default: 4)
```

```bash
$ npx --package @ncar/colors colors-hex-list -p div-RdBu -n 8
#67001f, #c1373a, #f09b7a, #fbe3d5, #dceaf2, #87beda, #3079b6, #053061

$ npx --package @ncar/colors colors-hex-list -p viridis-inv -n 3
#e6e808, #2993af, #440154
```

If the package is installed globally (`npm install -g @ncar/colors`), drop the `npx --package @ncar/colors`
prefix.
