<script>
	import { ui } from '../state.svelte.js';
	import { dataUrl } from '../data.js';
	import { splitColor } from '../heat.js';

	let { ex } = $props();
	const m = $derived(ex.meta);
	const S = $derived(m.n_splits);

	// Collapse runs of <image> tokens so the expanded prompt is readable.
	const expanded = $derived.by(() => {
		const out = [];
		for (const t of m.tokens.slice(0, m.prompt_len)) {
			const last = out[out.length - 1];
			if (t.kind === 'image' && last?.kind === 'image') last.n++;
			else out.push({ ...t, n: 1 });
		}
		return out;
	});
</script>

<div class="wrap">
	<div class="col">
		<div class="orig" style="aspect-ratio:{m.original_size[0]}/{m.original_size[1]}">
			<img src={dataUrl(`${m.id}/original.jpg`)} alt="Input" />
			{#each Array(m.rows * m.cols) as _, k}
				<button
					class="tilebox"
					class:sel={ui.split === k}
					style="left:{((k % m.cols) / m.cols) * 100}%;top:{(Math.floor(k / m.cols) / m.rows) * 100}%;width:{100 / m.cols}%;height:{100 / m.rows}%;--c:{splitColor(k, S)}"
					onclick={() => (ui.split = k)}
					aria-label="Split {k + 1}"
				></button>
			{/each}
		</div>
		<p class="hint">
			Original {m.original_size[0]}×{m.original_size[1]} → resized so the longest edge is 1024, then stretched to a
			{m.cols * 512}×{m.rows * 512} grid of 512px tiles.
		</p>
	</div>

	<div class="col">
		<div class="tiles" style="grid-template-columns:repeat({m.cols}, 1fr)">
			{#each Array(m.rows * m.cols) as _, k}
				<button class="tile" class:sel={ui.split === k} style="--c:{splitColor(k, S)}" onclick={() => (ui.split = k)}>
					<img src={dataUrl(`${m.id}/tiles/split_${k}.jpg`)} alt="Split {k + 1}" />
					<span>row {Math.floor(k / m.cols) + 1}, col {(k % m.cols) + 1}</span>
				</button>
			{/each}
		</div>
		<div class="plus">+ one downscaled copy of the whole image</div>
		<button class="tile global" class:sel={ui.split === S - 1} style="--c:{splitColor(S - 1, S)}" onclick={() => (ui.split = S - 1)}>
			<img src={dataUrl(`${m.id}/tiles/split_${S - 1}.jpg`)} alt="Global view" />
			<span>global</span>
		</button>
		<p class="hint">Tensor handed to the vision encoder: <span class="shape">[{S}, 3, 512, 512]</span></p>
	</div>

	<div class="col">
		<h3>What the text side sees</h3>
		<p class="hint">Chat template before expansion:</p>
		<pre class="mono">{m.chat_text}</pre>
		<p class="hint">
			After the processor expands the single <code>&lt;image&gt;</code> into {S} × 64 = {S * 64} placeholder tokens:
		</p>
		<div class="expanded">
			{#each expanded as t}
				{#if t.kind === 'image'}
					<span class="img" style="--c:{splitColor(t.split, S)}">&lt;image&gt;×{t.n}</span>
				{:else}
					<span class={t.kind}>{t.s}</span>
				{/if}
			{/each}
		</div>
	</div>
</div>

<style>
	.wrap {
		display: grid;
		grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr) minmax(0, 1.2fr);
		gap: 24px;
	}
	.orig {
		position: relative;
		width: 100%;
		border-radius: 8px;
		overflow: hidden;
	}
	.orig img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	.tilebox {
		position: absolute;
		border: 2px solid var(--c);
		background: transparent;
		cursor: pointer;
		padding: 0;
	}
	.tilebox.sel {
		border-width: 4px;
		background: color-mix(in srgb, var(--c) 15%, transparent);
	}
	.tiles {
		display: grid;
		gap: 8px;
	}
	.tile {
		position: relative;
		padding: 0;
		border: 3px solid var(--c);
		border-radius: 6px;
		overflow: hidden;
		cursor: pointer;
		background: none;
		opacity: 0.7;
		aspect-ratio: 1;
	}
	.tile.sel {
		opacity: 1;
		box-shadow: 0 0 0 3px var(--accent-soft);
	}
	.tile img {
		width: 100%;
		height: 100%;
		display: block;
	}
	.tile span {
		position: absolute;
		left: 4px;
		bottom: 4px;
		font-size: 10px;
		background: rgba(0, 0, 0, 0.6);
		color: white;
		padding: 0 4px;
		border-radius: 3px;
	}
	.global {
		width: 50%;
	}
	.plus {
		margin: 10px 0 6px;
		font-size: 13px;
		color: var(--muted);
	}
	h3 {
		margin: 0 0 6px;
		font-size: 15px;
	}
	pre {
		background: var(--surface-2);
		padding: 8px 10px;
		border-radius: 6px;
		white-space: pre-wrap;
		margin: 0 0 8px;
	}
	.expanded {
		display: flex;
		flex-wrap: wrap;
		gap: 3px;
		font-family: var(--mono);
		font-size: 11px;
	}
	.expanded span {
		padding: 1px 5px;
		border-radius: 4px;
		white-space: pre;
	}
	.special {
		background: var(--surface-2);
		color: var(--muted);
	}
	.text {
		background: color-mix(in srgb, var(--txt) 18%, transparent);
	}
	.img {
		background: var(--c);
		color: white;
	}
	@media (max-width: 1000px) {
		.wrap {
			grid-template-columns: 1fr;
		}
	}
</style>
