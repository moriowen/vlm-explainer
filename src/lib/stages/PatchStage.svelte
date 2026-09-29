<script>
	import { ui } from '../state.svelte.js';
	import { dataUrl } from '../data.js';
	import Tile from '../Tile.svelte';

	let { ex, config } = $props();
	const m = $derived(ex.meta);
	const v = $derived(config.vision);
	const side = $derived(v.image_size / v.patch); // 32

	let hover = $state(null);
	let pinned = $state(37 + 32 * 8);
	const patch = $derived(hover ?? pinned);
	const px = $derived(patch % side);
	const py = $derived(Math.floor(patch / side));

	const norms = $derived(m.patch_norms[ui.split]);
	const normHeat = $derived.by(() => {
		const lo = Math.min(...norms),
			hi = Math.max(...norms);
		return norms.map((n) => (n - lo) / (hi - lo || 1));
	});
	const tileSrc = $derived(dataUrl(`${m.id}/tiles/split_${ui.split}.jpg`));
</script>

<div class="wrap">
	<div class="col">
		<Tile
			src={tileSrc}
			size={360}
			gridSide={side}
			hoverSide={side}
			selected={pinned}
			onhover={(i) => (hover = i)}
			onpick={(i) => (pinned = i)}
			label="Split tile with 16px patch grid"
		/>
		<p class="hint">512 ÷ 16 = {side} patches per side → {side * side} patches. Hover or click one.</p>
	</div>

	<div class="col flow">
		<div class="step">
			<div class="zoom" style="background-image:url({tileSrc});background-size:{side * 100}%;background-position:{(px / (side - 1)) * 100}% {(py / (side - 1)) * 100}%"></div>
			<div class="lbl">patch ({py}, {px})<br /><span class="shape">16 × 16 × 3 = 768 values</span></div>
		</div>
		<div class="op">
			<code>Conv2d(3 → {v.hidden}, kernel=16, stride=16)</code>
			<span class="hint">one learned 16×16×3 filter per output channel, applied once per patch</span>
		</div>
		<div class="step">
			<div class="vec">
				{#each Array(48) as _, i}
					<span style="opacity:{0.25 + 0.75 * Math.abs(Math.sin(patch * 0.37 + i * 1.7))}"></span>
				{/each}
			</div>
			<div class="lbl">patch embedding<br /><span class="shape">[{v.hidden}]</span></div>
		</div>
		<div class="op">
			<code>+ position_embedding[{patch}]</code>
			<span class="hint">a learned vector for each of the {side * side} grid slots, so the encoder knows where every patch came from</span>
		</div>
		<p class="hint">
			The vector strip above is schematic; the real 768 numbers aren't drawn. Output for this split: <span class="shape">[1024, {v.hidden}]</span>, for all splits:
			<span class="shape">[{m.n_splits}, 1024, {v.hidden}]</span>.
		</p>
	</div>

	<div class="col">
		<div class="pair">
			<figure>
				<Tile src={tileSrc} size={200} dim heat={normHeat} heatSide={side} hoverSide={side} selected={patch} onhover={(i) => (hover = i)} label="Embedding norm" />
				<figcaption>Embedding size ‖x‖ per patch. Patches with edges and texture score high; flat regions score low.</figcaption>
			</figure>
			<figure>
				<Tile src={dataUrl(`${m.id}/pca/split_${ui.split}_l0.png`)} size={200} pixelated hoverSide={side} selected={patch} onhover={(i) => (hover = i)} label="PCA of patch embeddings" />
				<figcaption>The top 3 principal components of the 768-d embeddings, shown as RGB. Similar colors mean similar vectors.</figcaption>
			</figure>
		</div>
	</div>
</div>

<style>
	.wrap {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr) minmax(0, 1fr);
		gap: 24px;
		align-items: start;
	}
	.flow {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}
	.step {
		display: flex;
		gap: 12px;
		align-items: center;
	}
	.zoom {
		width: 96px;
		height: 96px;
		border-radius: 6px;
		border: 2px solid var(--accent);
		image-rendering: pixelated;
		background-repeat: no-repeat;
		flex: none;
	}
	.vec {
		width: 96px;
		display: grid;
		grid-template-columns: repeat(8, 1fr);
		gap: 2px;
		flex: none;
	}
	.vec span {
		aspect-ratio: 1;
		background: var(--accent);
		border-radius: 2px;
	}
	.lbl {
		font-size: 13px;
	}
	.op {
		border-left: 2px dashed var(--border);
		margin-left: 46px;
		padding: 4px 0 4px 16px;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.pair {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 14px;
	}
	figure {
		margin: 0;
	}
	figcaption {
		font-size: 12px;
		color: var(--muted);
		margin-top: 6px;
	}
	@media (max-width: 1100px) {
		.wrap {
			grid-template-columns: 1fr;
		}
	}
</style>
