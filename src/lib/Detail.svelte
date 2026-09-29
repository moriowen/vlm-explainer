<script>
	import { ui, STAGES } from './state.svelte.js';
	import { splitColor } from './heat.js';
	import ImageStage from './stages/ImageStage.svelte';
	import PatchStage from './stages/PatchStage.svelte';
	import VitStage from './stages/VitStage.svelte';
	import ConnectorStage from './stages/ConnectorStage.svelte';
	import MergeStage from './stages/MergeStage.svelte';
	import DecoderStage from './stages/DecoderStage.svelte';
	import OutputStage from './stages/OutputStage.svelte';

	let { ex, config } = $props();

	const idx = $derived(STAGES.findIndex((s) => s.id === ui.stage));
	const stage = $derived(STAGES[idx]);
	const usesSplit = $derived(['patch', 'vit', 'connector'].includes(ui.stage));
	const S = $derived(ex.meta.n_splits);
	const splitName = (k) => (k === S - 1 ? 'global' : `r${Math.floor(k / ex.meta.cols) + 1}c${(k % ex.meta.cols) + 1}`);

	function go(d) {
		const n = STAGES[idx + d];
		if (n) ui.stage = n.id;
	}
	function onkey(e) {
		if (e.target.closest('input, textarea')) return;
		if (e.key === 'ArrowRight') go(1);
		if (e.key === 'ArrowLeft') go(-1);
	}
</script>

<svelte:window onkeydown={onkey} />

<section class="detail card">
	<div class="bar">
		<button class="nav" disabled={idx === 0} onclick={() => go(-1)} aria-label="Previous stage">←</button>
		<h2><span class="n">{idx + 1}</span>{stage.name}</h2>
		<button class="nav" disabled={idx === STAGES.length - 1} onclick={() => go(1)} aria-label="Next stage">→</button>
		{#if usesSplit}
			<div class="splits">
				<span class="hint">Split</span>
				{#each Array(S) as _, k}
					<button
						class="pill"
						class:on={ui.split === k}
						style="--c:{splitColor(k, S)}"
						onclick={() => { ui.split = k; ui.query = null; }}
					><i></i>{splitName(k)}</button>
				{/each}
			</div>
		{/if}
	</div>
	<div class="body">
		{#if ui.stage === 'image'}
			<ImageStage {ex} />
		{:else if ui.stage === 'patch'}
			<PatchStage {ex} {config} />
		{:else if ui.stage === 'vit'}
			<VitStage {ex} {config} />
		{:else if ui.stage === 'connector'}
			<ConnectorStage {ex} {config} />
		{:else if ui.stage === 'merge'}
			<MergeStage {ex} {config} />
		{:else if ui.stage === 'decoder'}
			<DecoderStage {ex} {config} />
		{:else if ui.stage === 'output'}
			<OutputStage {ex} {config} />
		{/if}
	</div>
</section>

<style>
	.detail {
		margin-top: 8px;
		padding: 16px 18px 22px;
	}
	.bar {
		display: flex;
		align-items: center;
		gap: 10px;
		flex-wrap: wrap;
		margin-bottom: 14px;
	}
	h2 {
		margin: 0;
		font-size: 18px;
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.n {
		background: var(--accent);
		color: white;
		width: 24px;
		height: 24px;
		border-radius: 50%;
		display: grid;
		place-items: center;
		font-size: 13px;
	}
	.nav {
		border: 1px solid var(--border);
		background: var(--surface);
		border-radius: 6px;
		width: 30px;
		height: 30px;
		cursor: pointer;
	}
	.nav:disabled {
		opacity: 0.3;
		cursor: default;
	}
	.splits {
		margin-left: auto;
		display: flex;
		gap: 6px;
		align-items: center;
		flex-wrap: wrap;
	}
	.pill i {
		display: inline-block;
		width: 8px;
		height: 8px;
		border-radius: 2px;
		background: var(--c);
		margin-right: 5px;
	}
</style>
