<script>
	import { ui } from '../state.svelte.js';
	import { dataUrl, vitRow } from '../data.js';
	import Tile from '../Tile.svelte';

	let { ex, config } = $props();
	const m = $derived(ex.meta);
	const v = $derived(config.vision);

	let hoverQ = $state(null);
	const q = $derived(hoverQ ?? ui.query ?? 27);
	// attention exists for encoder layers 1..12; layer 0 (patch embedding) shows layer 1's attention
	const attnLayer = $derived(Math.max(1, ui.vitLayer));
	const heat = $derived(vitRow(ex, attnLayer - 1, ui.split, q));
	const ent = $derived(m.vit_attn_entropy);
	const entMax = $derived(Math.max(...ent));
	const entMin = $derived(Math.min(...ent));
</script>

<div class="wrap">
	<div class="col">
		<Tile
			src={dataUrl(`${m.id}/tiles/split_${ui.split}.jpg`)}
			size={380}
			dim
			{heat}
			heatSide={32}
			hoverSide={8}
			selected={q}
			onhover={(i) => (hoverQ = i)}
			onpick={(i) => (ui.query = i)}
			label="Attention heatmap"
		/>
		<p class="hint">
			Hover a 4×4 block of patches (it becomes one image token later) to see which patches it attends to in layer {attnLayer}.
			Click to pin it. Averaged over {v.heads} heads.
		</p>
	</div>

	<div class="col">
		<div class="layerpick">
			<span class="hint">Layer</span>
			<input type="range" min="0" max={v.layers} bind:value={ui.vitLayer} aria-label="Vision layer" />
			<span class="mono">{ui.vitLayer === 0 ? 'embed' : ui.vitLayer}</span>
		</div>
		<Tile
			src={dataUrl(`${m.id}/pca/split_${ui.split}_l${ui.vitLayer}.png`)}
			size={260}
			pixelated
			hoverSide={8}
			selected={q}
			onhover={(i) => (hoverQ = i)}
			onpick={(i) => (ui.query = i)}
			label="PCA of hidden states"
		/>
		<p class="hint">
			Hidden states after {ui.vitLayer === 0 ? 'the patch embedding' : `encoder layer ${ui.vitLayer}`}, projected to 3 principal
			components. Watch objects turn into solid regions of one color as the layers go up.
		</p>
	</div>

	<div class="col">
		<h3>Every layer</h3>
		<div class="strip">
			{#each Array(v.layers + 1) as _, l}
				<button class:on={ui.vitLayer === l} onclick={() => (ui.vitLayer = l)}>
					<img src={dataUrl(`${m.id}/pca/split_${ui.split}_l${l}.png`)} alt="Layer {l}" />
					<span>{l === 0 ? 'emb' : l}</span>
				</button>
			{/each}
		</div>
		<h3>How spread out is attention?</h3>
		<div class="ent">
			{#each ent as e, l}
				<button
					class:on={attnLayer === l + 1}
					style="height:{20 + 80 * ((e - entMin) / (entMax - entMin || 1))}%"
					onclick={() => (ui.vitLayer = l + 1)}
					title="Layer {l + 1}: entropy {e.toFixed(2)}"
					aria-label="Layer {l + 1}"
				></button>
			{/each}
		</div>
		<p class="hint">Mean attention entropy per layer. Taller bars mean attention spread over more of the image; shorter ones mean it's focused on a few patches.</p>
		<div class="block mono">
			<div>x = x + <b>Attention</b>(LayerNorm(x)) <span class="hint">{v.heads} heads × {v.hidden / v.heads}d</span></div>
			<div>x = x + <b>MLP</b>(LayerNorm(x)) <span class="hint">{v.hidden} → {v.mlp} → {v.hidden}, GELU</span></div>
			<div class="hint">bidirectional: every patch can attend to every other patch in its split</div>
		</div>
	</div>
</div>

<style>
	.wrap {
		display: grid;
		grid-template-columns: auto auto minmax(0, 1fr);
		gap: 24px;
		align-items: start;
	}
	.col {
		max-width: 400px;
	}
	.col:last-child {
		max-width: none;
	}
	.layerpick {
		display: flex;
		gap: 8px;
		align-items: center;
		margin-bottom: 8px;
	}
	.layerpick input {
		flex: 1;
	}
	h3 {
		font-size: 14px;
		margin: 0 0 8px;
	}
	.strip {
		display: grid;
		grid-template-columns: repeat(7, 1fr);
		gap: 4px;
		margin-bottom: 16px;
	}
	.strip button {
		padding: 0;
		border: 2px solid transparent;
		border-radius: 4px;
		background: none;
		cursor: pointer;
		position: relative;
		overflow: hidden;
	}
	.strip button.on {
		border-color: var(--accent);
	}
	.strip img {
		width: 100%;
		display: block;
		image-rendering: pixelated;
	}
	.strip span {
		position: absolute;
		left: 2px;
		top: 1px;
		font-size: 9px;
		color: white;
		text-shadow: 0 0 2px black;
	}
	.ent {
		display: flex;
		align-items: flex-end;
		gap: 3px;
		height: 60px;
	}
	.ent button {
		flex: 1;
		border: none;
		padding: 0;
		background: var(--special);
		border-radius: 2px 2px 0 0;
		cursor: pointer;
	}
	.ent button.on {
		background: var(--accent);
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
	@media (max-width: 1100px) {
		.wrap {
			grid-template-columns: 1fr;
		}
	}
</style>
