<script>
	import { ui } from '../state.svelte.js';
	import { rgb, splitColor } from '../heat.js';

	let { ex, config } = $props();
	const m = $derived(ex.meta);
	const S = $derived(m.n_splits);
	const len = $derived(m.steps[ui.step].seq_len);

	const groups = $derived.by(() => {
		const out = [];
		m.tokens.slice(0, len).forEach((t, pos) => {
			const last = out[out.length - 1];
			if (t.kind === 'image' && last?.kind === 'image' && last.split === t.split) last.qs.push(t.q);
			else if (t.kind === 'image') out.push({ kind: 'image', split: t.split, qs: [t.q], pos });
			else out.push({ ...t, pos });
		});
		return out;
	});
	const counts = $derived.by(() => {
		const c = { image: 0, text: 0, special: 0, gen: 0 };
		for (const t of m.tokens.slice(0, len)) c[t.kind]++;
		return c;
	});
	const show = (s) => (s === '\n' ? '\\n' : s);
</script>

<div class="wrap">
	<div class="explain">
		<div class="eq mono">
			<div><b>E</b> = embed_tokens(input_ids) <span class="shape">[{len}, {config.text.hidden}]</span></div>
			<div><b>E</b>[input_ids == &lt;image&gt;] = connector_out.flatten() <span class="shape">[{counts.image}, {config.text.hidden}]</span></div>
		</div>
		<p class="hint">
			There are no learned weights here. Text tokens are looked up in the vocabulary table as usual. Every
			<code>&lt;image&gt;</code> placeholder then has its embedding overwritten, in order, by one connector output. After
			that the decoder can't tell a word and an image patch apart except by where each sits in the sequence.
		</p>
		<div class="legend">
			<span><i style="background:var(--txt)"></i>text {counts.text}</span>
			<span><i style="background:var(--special)"></i>special {counts.special}</span>
			<span><i style="background:linear-gradient(90deg,#e4572e,#3c7dd9)"></i>image {counts.image}</span>
			<span><i style="background:var(--gen)"></i>generated so far {counts.gen}</span>
			<span class="hint">sequence length {len}</span>
		</div>
	</div>

	<div class="seq">
		{#each groups as gr}
			{#if gr.kind === 'image'}
				<div class="imgblock" style="--c:{splitColor(gr.split, S)}" title="split {gr.split + 1}: {gr.qs.length} image tokens at positions {gr.pos} to {gr.pos + gr.qs.length - 1}">
					{#each gr.qs as q}<span style="background:{rgb(ex.projColors[gr.split][q])}"></span>{/each}
				</div>
			{:else}
				<span class="tok {gr.kind}" title="position {gr.pos}, id {gr.id}">{show(gr.s)}</span>
			{/if}
		{/each}
		<span class="tok next">?</span>
	</div>
</div>

<style>
	.wrap {
		display: grid;
		grid-template-columns: minmax(260px, 0.8fr) minmax(0, 2fr);
		gap: 24px;
		align-items: start;
	}
	.eq {
		background: var(--surface-2);
		padding: 10px 12px;
		border-radius: 6px;
		display: grid;
		gap: 6px;
		font-size: 12px;
	}
	.legend {
		display: flex;
		flex-wrap: wrap;
		gap: 12px;
		font-size: 12px;
	}
	.legend i {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 2px;
		margin-right: 5px;
		vertical-align: -1px;
	}
	.seq {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
		align-items: center;
		font-family: var(--mono);
		font-size: 12px;
	}
	.tok {
		padding: 2px 5px;
		border-radius: 4px;
		white-space: pre;
	}
	.text {
		background: color-mix(in srgb, var(--txt) 20%, transparent);
	}
	.special {
		background: var(--surface-2);
		color: var(--muted);
		font-size: 10px;
	}
	.gen {
		background: color-mix(in srgb, var(--gen) 25%, transparent);
	}
	.next {
		border: 1.5px dashed var(--gen);
		color: var(--gen);
	}
	.imgblock {
		display: grid;
		grid-template-columns: repeat(8, 5px);
		gap: 1px;
		padding: 3px;
		border: 2px solid var(--c);
		border-radius: 4px;
	}
	.imgblock span {
		width: 5px;
		height: 5px;
	}
	@media (max-width: 900px) {
		.wrap {
			grid-template-columns: 1fr;
		}
	}
</style>
