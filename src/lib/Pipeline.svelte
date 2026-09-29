<script>
	import { ui, STAGES } from './state.svelte.js';
	import { dataUrl, softmaxTemp } from './data.js';
	import { rgb, splitColor } from './heat.js';

	let { ex, config } = $props();

	const m = $derived(ex.meta);
	const S = $derived(m.n_splits);
	const id = $derived(m.id);
	const step = $derived(m.steps[ui.step]);
	const probs = $derived(softmaxTemp(step.top, ui.temperature).slice(0, 5));
	const v = $derived(config.vision);
	const t = $derived(config.text);

	const shapes = $derived({
		image: `[${S}, 3, 512, 512]`,
		patch: `[${S}, 1024, ${v.hidden}]`,
		vit: `[${S}, 1024, ${v.hidden}]`,
		connector: `[${S}, 64, ${t.hidden}]`,
		merge: `[${step.seq_len}, ${t.hidden}]`,
		decoder: `[${step.seq_len}, ${t.hidden}]`,
		output: `[${t.vocab}]`
	});

	const seqCells = $derived(m.tokens.slice(0, step.seq_len + 1));
	const cellColor = (tk, i) => {
		if (i === step.seq_len) return 'var(--gen)';
		if (tk.kind === 'image') return rgb(ex.projColors[tk.split][tk.q]);
		if (tk.kind === 'special') return 'var(--special)';
		if (tk.kind === 'gen') return 'color-mix(in srgb, var(--gen) 55%, transparent)';
		return 'var(--txt)';
	};
</script>

<section class="pipeline" aria-label="Model pipeline">
	{#each STAGES as st, i (st.id)}
		{#if i > 0}
			<div class="arrow" aria-hidden="true"><span></span></div>
		{/if}
		<button class="stage card" class:on={ui.stage === st.id} onclick={() => (ui.stage = st.id)}>
			<div class="head">
				<span class="num">{i + 1}</span>
				<span class="name">{st.name}</span>
			</div>
			<div class="viz">
				{#if st.id === 'image'}
					<div class="orig" style="aspect-ratio:{m.original_size[0]}/{m.original_size[1]}">
						<img src={dataUrl(`${id}/original.jpg`)} alt="" />
						{#each Array(m.rows * m.cols) as _, k}
							<div
								class="tilebox"
								class:sel={ui.split === k}
								style="left:{((k % m.cols) / m.cols) * 100}%;top:{(Math.floor(k / m.cols) / m.rows) * 100}%;width:{100 / m.cols}%;height:{100 / m.rows}%;border-color:{splitColor(k, S)}"
							></div>
						{/each}
					</div>
					<div class="chips">
						{#each Array(S) as _, k}
							<span class="chip" style="background:{splitColor(k, S)}" class:sel={ui.split === k}></span>
						{/each}
					</div>
				{:else if st.id === 'patch'}
					<div class="sq">
						<img src={dataUrl(`${id}/tiles/split_${ui.split}.jpg`)} alt="" />
						<div class="grid32"></div>
					</div>
				{:else if st.id === 'vit'}
					<div class="sq"><img class="px" src={dataUrl(`${id}/pca/split_${ui.split}_l${ui.vitLayer}.png`)} alt="" /></div>
				{:else if st.id === 'connector'}
					<div class="sq"><img class="px" src={dataUrl(`${id}/proj/split_${ui.split}.png`)} alt="" /></div>
				{:else if st.id === 'merge'}
					<div class="seq">
						{#each seqCells as tk, k}
							<span style="background:{cellColor(tk, k)}"></span>
						{/each}
					</div>
				{:else if st.id === 'decoder'}
					<div class="bars">
						{#each step.img_mass as mass}
							<span style="height:{Math.max(2, mass * 100)}%"></span>
						{/each}
					</div>
					<div class="cap">attention on image, per layer</div>
				{:else if st.id === 'output'}
					<div class="probs">
						{#each probs as p}
							<div class="prow">
								<span class="ptok mono">{JSON.stringify(p.token).slice(1, -1)}</span>
								<span class="pbar"><span style="width:{p.p * 100}%"></span></span>
							</div>
						{/each}
					</div>
				{/if}
			</div>
			<span class="shape">{shapes[st.id]}</span>
		</button>
	{/each}
</section>

<style>
	.pipeline {
		display: flex;
		align-items: stretch;
		overflow-x: auto;
		padding: 4px 2px 12px;
		gap: 0;
	}
	.stage {
		flex: 1 1 0;
		min-width: 138px;
		padding: 10px;
		display: flex;
		flex-direction: column;
		gap: 8px;
		align-items: stretch;
		cursor: pointer;
		text-align: left;
		transition: border-color 0.15s, box-shadow 0.15s;
	}
	.stage:hover {
		border-color: var(--muted);
	}
	.stage.on {
		border-color: var(--accent);
		box-shadow: 0 0 0 3px var(--accent-soft);
	}
	.head {
		display: flex;
		gap: 6px;
		align-items: center;
		font-weight: 600;
		font-size: 13px;
	}
	.num {
		width: 18px;
		height: 18px;
		border-radius: 50%;
		background: var(--surface-2);
		display: grid;
		place-items: center;
		font-size: 11px;
		flex: none;
	}
	.stage.on .num {
		background: var(--accent);
		color: white;
	}
	.viz {
		flex: 1;
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: 6px;
		min-height: 110px;
	}
	.shape {
		align-self: flex-start;
	}
	.arrow {
		flex: 0 0 18px;
		display: grid;
		place-items: center;
	}
	.arrow span {
		width: 100%;
		height: 2px;
		background: var(--border);
		position: relative;
	}
	.arrow span::after {
		content: '';
		position: absolute;
		right: -1px;
		top: -4px;
		border: 5px solid transparent;
		border-left-color: var(--border);
		border-right: 0;
	}
	.orig {
		position: relative;
		width: 100%;
		border-radius: 4px;
		overflow: hidden;
	}
	.orig img,
	.sq img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	.tilebox {
		position: absolute;
		border: 1.5px solid;
		opacity: 0.8;
	}
	.tilebox.sel {
		border-width: 3px;
		opacity: 1;
	}
	.chips {
		display: flex;
		gap: 3px;
	}
	.chip {
		width: 12px;
		height: 12px;
		border-radius: 3px;
		opacity: 0.5;
	}
	.chip.sel {
		opacity: 1;
		outline: 2px solid var(--text);
	}
	.sq {
		position: relative;
		width: 100%;
		aspect-ratio: 1;
		border-radius: 4px;
		overflow: hidden;
	}
	.px {
		image-rendering: pixelated;
	}
	.grid32 {
		position: absolute;
		inset: 0;
		background-image: linear-gradient(to right, rgba(255, 255, 255, 0.22) 1px, transparent 1px),
			linear-gradient(to bottom, rgba(255, 255, 255, 0.22) 1px, transparent 1px);
		background-size: 3.125% 3.125%;
	}
	.seq {
		display: flex;
		flex-wrap: wrap;
		gap: 1px;
		align-content: center;
	}
	.seq span {
		width: 5px;
		height: 5px;
		border-radius: 1px;
	}
	.bars {
		height: 90px;
		display: flex;
		align-items: flex-end;
		gap: 1px;
	}
	.bars span {
		flex: 1;
		background: var(--img);
		border-radius: 1px 1px 0 0;
	}
	.cap {
		font-size: 11px;
		color: var(--muted);
	}
	.probs {
		display: grid;
		gap: 4px;
	}
	.prow {
		display: grid;
		grid-template-columns: 58px 1fr;
		gap: 4px;
		align-items: center;
	}
	.ptok {
		white-space: pre;
		overflow: hidden;
		text-overflow: ellipsis;
		font-size: 11px;
	}
	.pbar {
		height: 8px;
		background: var(--surface-2);
		border-radius: 2px;
		overflow: hidden;
	}
	.pbar span {
		display: block;
		height: 100%;
		background: var(--gen);
	}
</style>
