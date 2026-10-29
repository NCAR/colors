#!/usr/bin/env node
import { readFileSync } from 'fs';
import { join } from 'path';
import { Palette, intToHex } from './palette';

/**
 * Print a comma-separated list of hex values from a palette
 */
function cliHexListFromPalette(): void {
  const args = process.argv.slice(2);

  if (args.includes('-v') || args.includes('--version')) {
    const pkg = JSON.parse(readFileSync(join(__dirname, '..', 'package.json'), 'utf-8'));
    console.log(`colors v${pkg.version}`);
    return;
  }

  const value = (short: string, long: string): string | undefined => {
    const i = args.findIndex(a => a === short || a === long);
    return i >= 0 ? args[i + 1] : undefined;
  };

  const name = value('-p', '--palette');
  if (!name) {
    console.error('ERROR: --palette is required');
    process.exit(1);
  }
  const numColors = parseInt(value('-n', '--num-colors') ?? '4', 10);

  const { colorValues } = new Palette(name).interpolate(numColors);
  console.log(colorValues!.map(intToHex).join(', '));
}

cliHexListFromPalette();
