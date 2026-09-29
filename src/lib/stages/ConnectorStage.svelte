<script>
	import { ui } from '../state.svelte.js';
	import { dataUrl } from '../data.js';
	import { rgb } from '../heat.js';
	import Tile from '../Tile.svelte';

	let { ex, config } = $props();
	const m = $derived(ex.meta);
	const v = $derived(config.vision);
	const t = $derived(config.text);
	const sf = $derived(config.scale_factor);
	const g = $derived(32 / sf); // 8

	let hoverQ = $state(null);
	const q = $derived(hoverQ ?? ui.query ?? 27);
	const qr = $derived(Math.floor(q / g));
	const qc = $derived(q % g);
	const tileSrc = $derived(dataUrl(`${m.id}/tiles/split_${ui.split}.jpg`));
	const tokColor = $derived(rgb(ex.projColors[ui.split][q]));
	const norm = $derived(m.proj_norms[ui.split][q]);

	// 16 patch hues for the schematic, ordered the way pixel_shuffle concatenates them
	const hues = Array.from({ length: 16 }, (_, i) => `hsl(${(i * 360) / 16} 65% 58%)`);

	// Animate the 4x4 block collapsing into one long vector, over and over.
	let flat = $state(false);
	let sw = $state(480);
	$effect(() => {
		const id = setInterval(() => (flat = !flat), 1700);
		return () => clearInterval(id);
	});
	const cell = 25;
	function place(i, flat, sw) {
		if (!flat) return `left:${(i % 4) * (cell + 2)}px;top:${Math.floor(i / 4) * (cell + 2)}px;width:${cell}px;height:${cell}px`;
		const w = sw / 16;
		return `left:${i * w}px;top:124px;width:${w - 1}px;height:22px`;
	}
	const crop = (i) => {
		const r = qr * sf + Math.floor(i / 4);
		const c = qc * sf + (i % 4);
		return `background-image:url(${tileSrc});background-size:3200% 3200%;background-position:${(c / 31) * 100}% ${(r / 31) * 100}%`;
	};
</script>

<div class="wrap">
	<div class="col">
		<Tile
			src={tileSrc}
			size={300}
			gridSide={8}
			hoverSide={8}
			selected={q}
			onhover={(i) => (hoverQ = i)}
			onpick={(i) => (ui.query = i)}
			label="Tile grouped into 4x4 patch blocks"
		/>
		<p class="hint">{32}×{32} patch features, grouped into {g}×{g} blocks of {sf}×{sf}.</p>
	</div>

	<div class="col diagram">
		<div class="shuffle" bind:clientWidth={sw} aria-label="Pixel shuffle animation">
			{#each hues as h, i}
				<span style="{place(i, flat, sw)};{crop(i)};border-color:{h};transition-delay:{i * 25}ms"></span>
			{/each}
			<div class="stext">
				<b>Pixel shuffle</b>
				<div class="hint">16 neighbouring patches × {v.hidden} dims are stacked into one vector. No weights, just a reshape.</div>
				<div class="shape">[1024, {v.hidden}] → [{g * g}, {v.hidden * sf * sf}]</div>
			</div>
			<div class="dims"><span>0</span><span>{v.hidden * sf * sf} dims</span></div>
		</div>

		<div class="row">
			<div class="proj" aria-hidden="true">
				<svg viewBox="0 0 100 60" preserveAspectRatio="none"><polygon points="0,0 100,20 100,40 0,60" /></svg>
			</div>
			<div>
				<b>Modality projection</b>
				<div class="hint">A single linear layer, W ∈ ℝ<sup>{v.hidden * sf * sf}×{t.hidden}</sup>, maps the stacked vector into the language model's embedding space.</div>
				<div class="shape">[{g * g}, {v.hidden * sf * sf}] → [{g * g}, {t.hidden}]</div>
			</div>
		</div>

		<div class="row">
			<div class="token" style="background:{tokColor}"></div>
			<div>
				<b>Image token #{q}</b> <span class="hint">‖x‖ = {norm}</span>
				<div class="hint">Now the same width as a word embedding, ready to sit in the text sequence.</div>
			</div>
		</div>
	</div>

	<div class="col">
		<Tile
			src={dataUrl(`${m.id}/proj/split_${ui.split}.png`)}
			size={240}
			pixelated
			hoverSide={8}
			selected={q}
			onhover={(i) => (hoverQ = i)}
			onpick={(i) => (ui.query = i)}
			label="Projected image tokens"
		/>
		<p class="hint">
			The {g * g} image tokens for this split (PCA → RGB). Per split: 1024 patches become {g * g} tokens, {sf * sf}× fewer.
			All {m.n_splits} splits give <b>{m.n_splits * g * g}</b> image tokens.
		</p>
	</div>
</div>

<style>
	.wrap {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr) auto;
		gap: 28px;
		align-items: start;
	}
	.col {
		max-width: 320px;
	}
	.diagram {
		max-width: none;
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	.row {
		display: flex;
		gap: 14px;
		align-items: center;
	}
	.row > div:last-child {
		display: grid;
		gap: 3px;
	}
	.shuffle {
		position: relative;
		height: 164px;
	}
	.shuffle > span {
		position: absolute;
		border: 2px solid;
		border-radius: 3px;
		box-sizing: border-box;
		transition: all 0.7s cubic-bezier(0.65, 0, 0.35, 1);
	}
	.stext {
		position: absolute;
		left: 124px;
		top: 0;
		right: 0;
		display: grid;
		gap: 3px;
	}
	.shuffle .dims {
		position: absolute;
		left: 0;
		right: 0;
		top: 148px;
		margin: 0;
	}
	.dims {
		display: flex;
		justify-content: space-between;
		font-size: 11px;
		color: var(--muted);
		margin-top: -8px;
	}
	.proj {
		width: 104px;
		height: 60px;
		flex: none;
	}
	.proj svg {
		width: 100%;
		height: 100%;
	}
	.proj polygon {
		fill: var(--accent-soft);
		stroke: var(--accent);
		stroke-width: 1.5;
		vector-effect: non-scaling-stroke;
	}
	.token {
		width: 104px;
		height: 18px;
		flex: none;
		border-radius: 4px;
		margin-left: 0;
	}
	@media (max-width: 1100px) {
		.wrap {
			grid-template-columns: 1fr;
		}
	}
</style>
