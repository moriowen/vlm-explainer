import { base } from '$app/paths';

export const dataUrl = (path) => `${base}/data/${path}`;

export async function loadManifest() {
	const r = await fetch(dataUrl('manifest.json'));
	return r.json();
}

async function bin(path) {
	const r = await fetch(dataUrl(path));
	return new Uint8Array(await r.arrayBuffer());
}

/** Read an image into RGB triples, one per pixel. */
export async function loadPixels(path) {
	const img = new Image();
	img.src = dataUrl(path);
	await img.decode();
	const c = document.createElement('canvas');
	c.width = img.width;
	c.height = img.height;
	const ctx = c.getContext('2d');
	ctx.drawImage(img, 0, 0);
	const d = ctx.getImageData(0, 0, c.width, c.height).data;
	const out = [];
	for (let i = 0; i < d.length; i += 4) out.push([d[i], d[i + 1], d[i + 2]]);
	return out;
}

export async function loadExample(id) {
	const [meta, vitAttn, decAttn] = await Promise.all([
		fetch(dataUrl(`${id}/meta.json`)).then((r) => r.json()),
		bin(`${id}/vit_attn.bin`),
		bin(`${id}/dec_attn.bin`)
	]);
	const projColors = await Promise.all(
		Array.from({ length: meta.n_splits }, (_, s) => loadPixels(`${id}/proj/split_${s}.png`))
	);
	// position of every image token in the sequence, indexed [split][q]
	const imagePos = Array.from({ length: meta.n_splits }, () => new Array(64));
	meta.tokens.forEach((t, pos) => {
		if (t.kind === 'image') imagePos[t.split][t.q] = pos;
	});
	return { meta, vitAttn, decAttn, projColors, imagePos };
}

/** ViT attention, head-averaged: layer 0..11, query group 0..63 -> 1024 values in [0,1]. */
export function vitRow(ex, layer, split, q) {
	const S = ex.meta.n_splits;
	const start = ((layer * S + split) * 64 + q) * 1024;
	const out = new Float32Array(1024);
	for (let i = 0; i < 1024; i++) out[i] = ex.vitAttn[start + i] / 255;
	return out;
}

/** Decoder last-token attention for a step and layer. Returns raw-proportional values (max = 1). */
export function decRow(ex, step, layer) {
	const len = ex.meta.steps[step].seq_len;
	const start = ex.meta.dec_offsets[step] + layer * len;
	const out = new Float32Array(len);
	for (let i = 0; i < len; i++) {
		const v = ex.decAttn[start + i] / 255;
		out[i] = v * v; // stored sqrt-scaled
	}
	return out;
}

/** Average of decRow over all layers. */
export function decRowAvg(ex, step, layers) {
	const len = ex.meta.steps[step].seq_len;
	const out = new Float32Array(len);
	for (let l = 0; l < layers; l++) {
		const r = decRow(ex, step, l);
		for (let i = 0; i < len; i++) out[i] += r[i] / layers;
	}
	return out;
}

/**
 * Map a sequence attention row onto per-split 8x8 grids, normalized over image tokens.
 * Scaled to the 97th percentile so one outlier token doesn't wash out the rest.
 */
export function rowToImageGrids(ex, row) {
	const grids = ex.imagePos.map((ps) => ps.map((p) => (p < row.length ? row[p] : 0)));
	const sorted = grids.flat().sort((a, b) => a - b);
	const ref = sorted[Math.floor(sorted.length * 0.97)] || sorted[sorted.length - 1];
	return grids.map((g) => g.map((v) => (ref ? Math.min(1, v / ref) : 0)));
}

export function softmaxTemp(top, temp) {
	const logits = top.map((t) => t[2] / Math.max(temp, 1e-3));
	const m = Math.max(...logits);
	const e = logits.map((l) => Math.exp(l - m));
	const z = e.reduce((a, b) => a + b, 0);
	return top.map((t, i) => ({ token: t[0], id: t[1], logit: t[2], p: e[i] / z }));
}
