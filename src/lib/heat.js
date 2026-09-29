import { interpolateInferno, interpolateRdBu } from 'd3-scale-chromatic';

/** Paint a side x side grid of [0,1] values onto a canvas as a translucent heatmap. */
export function paintHeat(canvas, values, side, { alpha = 0.75, gamma = 0.6 } = {}) {
	if (!canvas) return;
	const ctx = canvas.getContext('2d');
	const w = canvas.width,
		h = canvas.height;
	ctx.clearRect(0, 0, w, h);
	if (!values) return;
	const cw = w / side,
		ch = h / side;
	for (let i = 0; i < side * side; i++) {
		const v = Math.pow(values[i], gamma);
		ctx.globalAlpha = alpha * Math.min(1, v * 1.4);
		ctx.fillStyle = interpolateInferno(0.15 + 0.85 * v);
		ctx.fillRect((i % side) * cw, Math.floor(i / side) * ch, Math.ceil(cw), Math.ceil(ch));
	}
	ctx.globalAlpha = 1;
}

export const heatColor = (v) => interpolateInferno(0.1 + 0.9 * Math.max(0, Math.min(1, v)));

/** Diverging color for a vector component in [-127, 127]. */
export const vecColor = (v) => interpolateRdBu(0.5 - (v / 127) * 0.5);

export const rgb = (c) => (c ? `rgb(${c[0]},${c[1]},${c[2]})` : 'transparent');

/** Per-split colors: [strong, pastel]. The global view is always the last split. */
const SPLITS = [
	['#ec7a4b', '#fbd5c3'],
	['#2fa574', '#bde8d2'],
	['#4a86e0', '#c9dcf8'],
	['#d19b12', '#f3e2a8'],
	['#9b6be0', '#e0d0f7'],
	['#d6589a', '#f5cde2'],
	['#3aa8b0', '#c3e9ec'],
	['#8a8f3c', '#e3e5c2']
];
const GLOBAL = ['#687489', '#d5dae4'];
export const TEXT = ['#5f6fb0', '#d7dcf2'];
export const DEC = ['#7c5ce0', '#ddd3fa'];
export const OUT = ['#25a36a', '#c4ecd8'];

export const splitPair = (s, n) => (s === n - 1 ? GLOBAL : SPLITS[s % SPLITS.length]);
export const splitColor = (s, n) => splitPair(s, n)[0];
export const splitLight = (s, n) => splitPair(s, n)[1];
