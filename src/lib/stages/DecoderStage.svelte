<script>
	import { ui } from '../state.svelte.js';
	import { dataUrl, decRow, decRowAvg, rowToImageGrids } from '../data.js';
	import { heatColor, splitColor } from '../heat.js';
	import Tile from '../Tile.svelte';

	let { ex, config } = $props();
	const m = $derived(ex.meta);
	const t = $derived(config.text);
	const S = $derived(m.n_splits);
	const step = $derived(m.steps[ui.step]);
	const L = $derived(t.layers);

	const row = $derived(ui.decLayer < 0 ? decRowAvg(ex, ui.step, L) : decRow(ex, ui.step, ui.decLayer));
	const grids = $derived(rowToImageGrids(ex, row));
	const mass = $derived(
		ui.decLayer < 0 ? step.img_mass.reduce((a, b) => a + b, 0) / L : step.img_mass[ui.decLayer]
	);

	const textToks = $derived(
		m.tokens.slice(0, step.seq_len).map((tk, pos) => ({ ...tk, pos, a: row[pos] })).filter((tk) => tk.kind !== 'image')
	);
	// Skip the first token (attention sink) when scaling so the rest stays visible.
	const textMax = $derived(Math.max(1e-9, ...textToks.slice(1).map((x) => x.a)));
	const show = (s) => (s === '\n' ? '\\n' : s);
	const clean = (s) => JSON.stringify(s).slice(1, -1);
	const lensLayer = $derived(ui.decLayer < 0 ? L - 1 : ui.decLayer);
</script>

<div class="top">
	<div class="predict">
		Predicting token {ui.step + 1}: <span class="gen mono">{clean(step.token)}</span>
		<span class="hint">· {ui.decLayer < 0 ? `averaged over all ${L} layers` : `layer ${ui.decLayer + 1}`} · {(mass * 100).toFixed(1)}% of attention lands on image tokens</span>
	</div>
	<div class="layers">
		<button class="pill" class:on={ui.decLayer < 0} onclick={() => (ui.decLayer = -1)}>All layers</button>
		<div class="bars" role="group" aria-label="Decoder layers">
			{#each step.img_mass as mm, l}
				<button
					class:on={ui.decLayer === l}
					onclick={() => (ui.decLayer = l)}
					title="Layer {l + 1}: {(mm * 100).toFixed(1)}% on image"
					aria-label="Layer {l + 1}"
				><span style="height:{Math.max(3, mm * 100)}%"></span></button>
			{/each}
		</div>
		<span class="hint">Share of attention on image tokens, per layer. Click a bar.</span>
	</div>
</div>

<div class="wrap">
	<div class="col">
		<h3>Where it looks in the image</h3>
		<div class="tiles" style="grid-template-columns:repeat({m.cols}, 1fr)">
			{#each Array(m.rows * m.cols) as _, k}
				<div class="tw" style="--c:{splitColor(k, S)}">
					<Tile src={dataUrl(`${m.id}/tiles/split_${k}.jpg`)} size={170} dim heat={grids[k]} heatSide={8} label="Split {k + 1} attention" />
				</div>
			{/each}
		</div>
		<div class="tw global" style="--c:{splitColor(S - 1, S)}">
			<Tile src={dataUrl(`${m.id}/tiles/split_${S - 1}.jpg`)} size={170} dim heat={grids[S - 1]} heatSide={8} label="Global attention" />
			<span class="hint">global view</span>
		</div>
		<p class="hint">Each cell is one image token (one 4×4 patch block). Scaled to the brightest image token.</p>
	</div>

	<div class="col">
		<h3>…and in the text</h3>
		<div class="text">
			{#each textToks as tk, i}
				<span
					class="tok"
					class:sink={i === 0}
					style="background:{i === 0 ? 'var(--surface-2)' : heatColor(tk.a / textMax)};color:{i > 0 && tk.a / textMax > 0.55 ? '#111' : ''}"
					title="position {tk.pos}: {(tk.a * 100).toFixed(2)}% of max"
				>{show(tk.s)}</span>
			{/each}
			<span class="tok cur">{clean(step.token)}</span>
		</div>
		<p class="hint">
			The first token usually takes a big share of attention as an "attention sink" (grey here), so the colors are scaled
			without it. Image tokens are hidden in this view.
		</p>
		<div class="block mono">
			<div>x = x + <b>CausalAttention</b>(RMSNorm(x)) <span class="hint">{t.heads} query heads, {t.kv_heads} KV heads (GQA), RoPE</span></div>
			<div>x = x + <b>SwiGLU MLP</b>(RMSNorm(x)) <span class="hint">{t.hidden} → {t.mlp} → {t.hidden}</span></div>
			<div class="hint">×{L} layers, then RMSNorm → lm_head → {t.vocab.toLocaleString()} logits</div>
		</div>
	</div>

	<div class="col">
		<h3>Logit lens</h3>
		<p class="hint">If we stopped after layer <i>n</i> and decoded straight away, what would come out?</p>
		<div class="lens">
			{#each step.lens as top, l}
				<button class="lrow" class:on={l === lensLayer} onclick={() => (ui.decLayer = l)}>
					<span class="ln">{l + 1}</span>
					<span class="lt mono" class:hit={top[0][0] === step.token}>{clean(top[0][0])}</span>
					<span class="lb"><span style="width:{top[0][1] * 100}%"></span></span>
				</button>
			{/each}
		</div>
	</div>
</div>

<style>
	.top {
		display: grid;
		gap: 10px;
		margin-bottom: 18px;
	}
	.gen {
		background: var(--gen);
		color: white;
		padding: 1px 6px;
		border-radius: 4px;
		white-space: pre;
	}
	.layers {
		display: flex;
		align-items: center;
		gap: 12px;
		flex-wrap: wrap;
	}
	.bars {
		display: flex;
		align-items: flex-end;
		gap: 2px;
		height: 44px;
		flex: 1;
		min-width: 240px;
		max-width: 520px;
	}
	.bars button {
		flex: 1;
		height: 100%;
		border: none;
		padding: 0;
		background: none;
		display: flex;
		align-items: flex-end;
		cursor: pointer;
	}
	.bars button span {
		width: 100%;
		background: color-mix(in srgb, var(--img) 55%, transparent);
		border-radius: 2px 2px 0 0;
	}
	.bars button.on span {
		background: var(--img);
		outline: 2px solid var(--text);
	}
	.wrap {
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) 240px;
		gap: 24px;
		align-items: start;
	}
	h3 {
		margin: 0 0 8px;
		font-size: 14px;
	}
	.tiles {
		display: grid;
		gap: 6px;
		max-width: 360px;
	}
	.tw {
		border: 2px solid var(--c);
		border-radius: 8px;
		line-height: 0;
	}
	.global {
		margin-top: 8px;
		width: fit-content;
		display: flex;
		align-items: end;
		gap: 8px;
		line-height: 1.4;
		border: none;
	}
	.global :global(.tile) {
		border: 2px solid var(--c);
	}
	.text {
		display: flex;
		flex-wrap: wrap;
		gap: 3px;
		font-size: 12px;
		font-family: var(--mono);
	}
	.tok {
		padding: 2px 4px;
		border-radius: 3px;
		white-space: pre;
		color: white;
	}
	.sink {
		color: var(--muted);
	}
	.cur {
		background: none;
		border: 1.5px dashed var(--gen);
		color: var(--gen);
	}
	.block {
		margin-top: 14px;
		background: var(--surface-2);
		padding: 10px 12px;
		border-radius: 6px;
		display: grid;
		gap: 4px;
		font-size: 12px;
	}
	.lens {
		display: grid;
		gap: 1px;
		max-height: 520px;
		overflow-y: auto;
	}
	.lrow {
		display: grid;
		grid-template-columns: 22px 90px 1fr;
		gap: 6px;
		align-items: center;
		border: none;
		background: none;
		padding: 1px 4px;
		border-radius: 4px;
		cursor: pointer;
		text-align: left;
	}
	.lrow.on {
		background: var(--accent-soft);
	}
	.ln {
		font-size: 11px;
		color: var(--muted);
	}
	.lt {
		white-space: pre;
		overflow: hidden;
		text-overflow: ellipsis;
		font-size: 12px;
	}
	.lt.hit {
		color: var(--gen);
		font-weight: 700;
	}
	.lb {
		height: 7px;
		background: var(--surface-2);
		border-radius: 2px;
		overflow: hidden;
	}
	.lb span {
		display: block;
		height: 100%;
		background: var(--accent);
	}
	@media (max-width: 1100px) {
		.wrap {
			grid-template-columns: 1fr;
		}
	}
</style>
