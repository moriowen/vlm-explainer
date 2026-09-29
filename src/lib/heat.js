import { interpolateInferno } from 'd3-scale-chromatic';

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

export const rgb = (c) => (c ? `rgb(${c[0]},${c[1]},${c[2]})` : 'transparent');

/** Colors for image splits (tiles). The global view is always the last split. */
const SPLIT_COLORS = ['#e4572e', '#29a36a', '#3c7dd9', '#c9a227', '#a05cd6', '#d6589a', '#4cb3b8', '#8a8f3c'];
export const splitColor = (s, n) => (s === n - 1 ? '#7a7a8c' : SPLIT_COLORS[s % SPLIT_COLORS.length]);
