<script>
	import { rgb, splitColor, heatColor } from '../heat.js';
	import { ui } from '../state.svelte.js';

	/**
	 * The merged token sequence, laid out as segments.
	 * mode 'embed': image tokens in projection colors. mode 'attn': everything colored by attention.
	 */
	let { ex, len, segments, mode = 'embed', row = null, grids = null, pending = null, prefix = 'seq' } = $props();

	const m = $derived(ex.meta);
	const S = $derived(m.n_splits);

	const show = (s) => (/^\n+$/.test(s) ? '⏎'.repeat(s.length) : s.replace('<fake_token_around_image>', '◇').replace('<end_of_utterance>', '⟨eou⟩').replace('<|im_start|>', '⟨start⟩'));

	const textMax = $derived.by(() => {
		if (!row) return 1;
		let mx = 1e-9;
		m.tokens.slice(1, len).forEach((t, i) => {
			if (t.kind !== 'image') mx = Math.max(mx, row[i + 1]);
		});
		return mx;
	});
	const chipStyle = (t) => {
		if (mode !== 'attn' || !row) return '';
		if (t.pos === 0) return 'background:var(--chip);color:var(--muted)';
		const v = Math.min(1, row[t.pos] / textMax);
		return `background:${heatColor(v)};color:${v > 0.55 ? '#111' : '#fff'};border-color:transparent`;
	};
	const cellColor = (s, q) => (mode === 'attn' && grids ? heatColor(grids[s][q]) : rgb(ex.projColors[s][q]));
</script>

<div class="seq {mode}">
	{#each segments as seg, i}
		{#if seg.type === 'image'}
			<div class="img" data-rib="{prefix}-img-{seg.split}" style="--c:{splitColor(seg.split, S)}" class:traced={ui.hover === `split-${seg.split}`}>
				<div class="grid">
					{#each seg.qs as q}<span style="background:{cellColor(seg.split, q)}"></span>{/each}
				</div>
				<span class="lbl">{seg.split === S - 1 ? 'global' : `tile ${seg.split + 1}`}<br /><b>{seg.qs.length}</b> tokens</span>
			</div>
		{:else}
			<div class="chips {seg.kind}" data-rib="{prefix}-seg-{i}">
				{#each seg.toks as t}
					<span class="chip {t.kind}" class:query={mode === 'attn' && t.pos === len - 1} data-rib="{prefix}-tok-{t.pos}" style={chipStyle(t)} title="#{t.pos} · id {t.id} · {JSON.stringify(t.s)}">{show(t.s)}</span>
				{/each}
			</div>
		{/if}
	{/each}
	<div class="chips pending-row">
		<span class="chip next" data-rib="{prefix}-next" class:filled={pending}>{pending ? show(pending) : '?'}</span>
	</div>
</div>

<style>
	.seq {
		display: flex;
		flex-direction: column;
		gap: 5px;
		font-family: var(--mono);
		font-size: 10.5px;
	}
	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 2px;
	}
	.chip {
		padding: 0 4px;
		line-height: 15px;
		border-radius: 3px;
		white-space: pre;
		background: var(--chip-text);
		border: 1px solid transparent;
		transition: background 0.25s;
	}
	.chip.special {
		background: var(--chip);
		color: var(--muted);
		font-size: 9.5px;
	}
	.chip.gen {
		background: var(--chip-gen);
	}
	.chips.tag .chip {
		font-size: 9px;
		line-height: 12px;
	}
	.chip.query {
		outline: 2px solid var(--out);
		outline-offset: 1px;
	}
	.next {
		border: 1.5px dashed var(--out);
		color: var(--out);
		background: transparent;
		min-width: 22px;
		text-align: center;
	}
	.next.filled {
		background: var(--out);
		color: white;
		border-style: solid;
	}
	.img {
		display: flex;
		gap: 8px;
		align-items: center;
		padding: 3px;
		border-left: 3px solid var(--c);
		border-radius: 3px;
		background: var(--surface);
		transition: box-shadow 0.2s;
	}
	.img.traced {
		box-shadow: 0 0 0 2px var(--c);
	}
	.grid {
		display: grid;
		grid-template-columns: repeat(8, 5px);
		grid-auto-rows: 5px;
		gap: 0;
		flex: none;
	}
	.grid span {
		transition: background 0.25s;
	}
	.lbl {
		font-family: var(--sans);
		font-size: 10px;
		color: var(--muted);
		line-height: 1.25;
	}
	.lbl b {
		color: var(--text);
	}
</style>
