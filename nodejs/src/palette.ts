import { stringify } from 'yaml';
import palettesData from './resources/palettes.json';

export type ColorFormat = 'hex' | 'int' | 'float';

/**
 * Load the palette definitions from the bundled JSON resource.
 * Upper and lower case variants of every name are added, like the Python package does.
 */
function loadPalettes(): Record<string, string[]> {
  const data: Record<string, string[]> = { ...palettesData };
  for (const key of Object.keys(data)) {
    const upper = key.toUpperCase();
    const lower = key.toLowerCase();
    if (!(upper in data)) data[upper] = data[key];
    if (!(lower in data)) data[lower] = data[key];
  }
  return data;
}

/**
 * Create evenly spaced values over an interval
 */
export function linspace(start: number, stop: number, num: number): number[] {
  if (num === 1) return [stop];
  return Array.from({ length: num }, (_, i) => start + (stop - start) * i / (num - 1));
}

/**
 * Perform 1D linear interpolation
 */
export function interp(x: number[], xp: number[], fp: number[]): number[] {
  return x.map(xi => {
    if (xi <= xp[0]) return fp[0];
    if (xi >= xp[xp.length - 1]) return fp[fp.length - 1];
    for (let j = 0; j < xp.length - 1; j++) {
      if (xp[j] <= xi && xi <= xp[j + 1]) {
        return fp[j] + (xi - xp[j]) * (fp[j + 1] - fp[j]) / (xp[j + 1] - xp[j]);
      }
    }
    return fp[fp.length - 1];
  });
}

/**
 * Stack channel arrays into rows of RGB triples, clamped to 0-255
 */
export function stack(arrays: number[][]): number[][] {
  return arrays[0].map((_, j) => arrays.map(arr => Math.max(0, Math.min(255, Math.round(arr[j])))));
}

export function hexToInt(hexCode: string): number[] {
  const code = hexCode.replace(/^#/, '');
  return [0, 2, 4].map(i => parseInt(code.substring(i, i + 2), 16));
}

export function intToHex(rgb: number[]): string {
  return '#' + rgb.slice(0, 3).map(c => c.toString(16).padStart(2, '0')).join('');
}

export function intToInt(rgb: number[]): number[] {
  return rgb.slice(0, 3).map(c => Math.trunc(c));
}

export function intToFloat(rgb: number[]): number[] {
  return rgb.slice(0, 3).map(c => c / 255.0);
}

export function hexToFloat(hexCode: string): number[] {
  return intToFloat(hexToInt(hexCode));
}

export function floatToHex(rgb: number[]): string {
  return intToHex(rgb.slice(0, 3).map(c => Math.min(255, Math.max(0, Math.round(c * 255)))));
}

/**
 * Class that handles color palettes and associated operations
 */
export class Palette {
  static PALETTES: Record<string, string[]> = loadPalettes();

  name: string | null;
  colorValues: number[][] | null;
  scales: Scale[] = [];

  /**
   * @param name Palette name to load. Append '-inv' to invert it
   * @param defaultName Backup palette to load if the first is not found
   */
  constructor(name: string | null = null, defaultName: string | null = null) {
    this.name = name;
    this.colorValues = Palette.getPaletteValues(name, defaultName);
  }

  /** Number of colors in this palette, or -1 if it is empty */
  get nColors(): number {
    return this.colorValues === null ? -1 : this.colorValues.length;
  }

  get yamlHex(): string {
    return Palette.toYaml(this.name, this.colorValues, 'hex');
  }

  get yamlInt(): string {
    return Palette.toYaml(this.name, this.colorValues, 'int');
  }

  get yamlFloat(): string {
    return Palette.toYaml(this.name, this.colorValues, 'float');
  }

  /**
   * Get RGB integer triples for a named palette
   * @returns null if the palette name is not found
   */
  static getPaletteValues(name: string | null, defaultName: string | null = null): number[][] | null {
    if (name === null && defaultName === null) return null;
    if (name === null) return Palette.getPaletteValues(defaultName);

    // check for an inverted palette
    const invert = name.endsWith('-inv');
    const base = invert ? name.slice(0, -4) : name;

    for (const candidate of [base, base.toLowerCase(), base.toUpperCase()]) {
      if (Object.prototype.hasOwnProperty.call(Palette.PALETTES, candidate)) {
        const rgb = Palette.PALETTES[candidate].map(hexToInt);
        return invert ? rgb.reverse() : rgb;
      }
    }
    if (defaultName !== null) return Palette.getPaletteValues(defaultName);

    console.warn(`WARN: Invalid palette name: ${base}`);
    return null;
  }

  /**
   * Convert palette values to a YAML string
   */
  static toYaml(name: string | null, values: number[][] | null, colorFormat: ColorFormat = 'hex'): string {
    if (name === null || values === null) return '';
    const convert = { hex: intToHex, int: intToInt, float: intToFloat }[colorFormat];
    return stringify({ [name]: values.map(rgb => convert(rgb)) }, { indent: 2 });
  }

  /**
   * Interpolate this palette to a specified number of colors
   * @returns A new Palette with the interpolated colors
   */
  interpolate(nColors: number): Palette {
    if (this.colorValues === null) throw new Error('Cannot interpolate an empty palette');
    const xp = linspace(0, 1, this.colorValues.length);
    const x = linspace(0, 1, nColors);
    const channels = [0, 1, 2].map(c => interp(x, xp, this.colorValues!.map(rgb => rgb[c])));

    const palette = new Palette();
    palette.name = this.name;
    palette.colorValues = stack(channels);
    return palette;
  }


  /**
   * Get a linear-gradient for a CSS background-image
   * @returns A string that can be used as the background-image value in CSS
   */
  getLinearGradient(): string {
    /* make sure we have colors in the palette */
    if (this.colorValues === null)
      return '';

    /* width of each segment as a percentage */
    const width: number = 100 / this.colorValues.length;

    /* empty string to store the list of rgb values */
    let colors = '';

    /* position on the gradient as a percentage */
    let position: number = 0;
    for (let color of this.colorValues)
    {
      /* add this color to the linear gradient */
      colors += ', rgb(' + color[0] + ',' + color[1] + ',' + color[2] + ') ' + position + '% ' + (position+width) + '%';

      /* increment the width */
      position += width;
    }

    return 'linear-gradient(90deg' + colors + ')';
  }
}

export interface ScaleOptions {
  label?: string;
  position?: string;
  fontFamily?: string;
  fontSize?: number;
  color?: string | number[];
  backgroundColor?: number[];
  padding?: number[];
  margin?: number[];
  min?: number;
  max?: number;
  ticks?: number;
  precision?: number;
}

/**
 * Describes the value range (and display options) a palette is stretched across
 */
export class Scale {
  label: string | null;
  position: string;
  fontFamily: string;
  fontSize: number;
  color: number[];
  backgroundColor: number[] | null;
  padding: number[];  // follows CSS: top, right, bottom, left
  margin: number[];   // follows CSS: top, right, bottom, left
  min: number | null;
  max: number | null;
  ticks: number | null;
  precision: number;

  constructor(data: ScaleOptions = {}) {
    this.label = data.label ?? null;
    this.position = data.position ?? 'lower';
    this.fontFamily = data.fontFamily ?? 'Arial';
    this.fontSize = data.fontSize ?? 12;
    this.color = typeof data.color === 'string' ? hexToInt(data.color) : data.color ?? [0, 0, 0];
    this.backgroundColor = data.backgroundColor ?? null;
    this.padding = data.padding ?? [10, 10, 10, 10];
    this.margin = data.margin ?? [0, 0, 0, 0];
    this.min = data.min ?? null;
    this.max = data.max ?? null;
    this.ticks = data.ticks ?? null;
    this.precision = data.precision ?? 1;
  }
}

/**
 * Uses a Palette and Scale to retrieve a color value
 */
export class ColorMap {
  constructor(public palette: Palette, public scale: Scale) {}

  /**
   * Normalize a value between xMin and xMax to an index in 0..n-1
   */
  private static normalize(x: number, xMin: number, xMax: number, n: number): number {
    if (x >= xMax) return n - 1;
    if (x <= xMin) return 0;
    return Math.round(((x - xMin) / (xMax - xMin)) * (n - 1));
  }

  /**
   * Get a color for a value using the Palette and Scale given to the constructor
   * @param x Value to map to a color
   * @param colorFormat 'hex' (default), 'int' or 'float'
   */
  mapColor(x: number, colorFormat: 'hex'): string;
  mapColor(x: number, colorFormat: 'int' | 'float'): number[];
  mapColor(x: number): string;
  mapColor(x: number, colorFormat: ColorFormat = 'hex'): string | number[] {
    const { colorValues } = this.palette;
    const { min, max } = this.scale;
    if (colorValues === null) throw new Error('Palette has no colors');
    if (min === null || max === null) throw new Error('Scale min and max must be set');

    const rgb = colorValues[ColorMap.normalize(x, min, max, colorValues.length)];
    switch (colorFormat) {
      case 'hex': return intToHex(rgb);
      case 'int': return intToInt(rgb);
      case 'float': return intToFloat(rgb);
      default: throw new Error('Invalid color format');
    }
  }
}
