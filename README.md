# colors

Color palettes, value-to-color mapping, and legend graphics, for Python and NodeJS.

## Introduction

`colors` manages a library of named color palettes (sequential, diverging, and several
weather-specific sets such as radar reflectivity, CAPE, and wind speed) and gives you the tools to
put them to work:

- **Palettes** – look up a palette by name, get its colors as hex, integer RGB, or float RGB, reverse it
  by appending `-inv` to its name, and resample it to any number of colors.
- **Color mapping** – map a numeric value onto a palette over a `[min, max]` range. Values outside
  the range clamp to the end colors.
- **Legends** – describe a scale (label, ticks, precision, fonts) and render a PNG legend graphic
  *(Python only)*.

The project ships two sibling packages that share the same palette definitions and the same
concepts, so a map drawn by a Python service and a UI built in NodeJS agree on every color.

| Feature                               | Python (`colors`)                                | NodeJS (`@ncar/colors`) |
|---------------------------------------|--------------------------------------------------|-------------------------|
| Palette lookup, `-inv`, interpolation | yes                                              | yes                     |
| Value → color (`ColorMap`)            | yes                                              | yes                     |
| Hex / int / float conversion          | yes                                              | yes                     |
| `Scale` configuration                 | yes                                              | yes                     |
| PNG legend rendering                  | yes (optional `legend` extra)                    | no                      |
| CSS gradient for web front-ends       | –                                                | yes (see example)       |
| Command line tools                    | `colors-hex`, `colors-legend`, `colors-swatches` | `colors-hex-list`       |

```
.
├── python/    # the Python package    -> python/README.md
└── nodejs/    # the NodeJS package    -> nodejs/README.md
```

## Examples

Each package has its own README with complete, runnable examples.

### Python (CLI)

`colors-hex`, `colors-legend`, and `colors-swatches`: see
[How To Use CLI](python/README.md#how-to-use-cli).

### Python (code)

Mapping values to colors, working with palettes, and drawing legend graphics: see
[How To Use As Library](python/README.md#how-to-use-as-library).

### NodeJS (CLI)

`colors-hex-list`: see [How To Use CLI](nodejs/README.md#how-to-use-cli).

### NodeJS (code)

Mapping values to colors and working with palettes, including rendering a palette as a CSS
`linear-gradient(...)` for a web front-end: see
[How To Use As Library](nodejs/README.md#how-to-use-as-library).

## Installation Steps

### Python

See [How To Install](python/README.md#how-to-install) (Python 3.11 or newer; the `legend` extra adds
PNG legend rendering).

### NodeJS

See [How To Install](nodejs/README.md#how-to-install).

## How to Contribute

Contributions are welcome, from new palettes to bug fixes and documentation.

Please open an issue first for large changes so the approach can be discussed before you invest
the time.
