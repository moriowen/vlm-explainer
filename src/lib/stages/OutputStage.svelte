<script>
	import { ui } from '../state.svelte.js';
	import { softmaxTemp } from '../data.js';

	let { ex, config } = $props();
	const step = $derived(ex.meta.steps[ui.step]);
	const probs = $derived(softmaxTemp(step.top, ui.temperature));
	const lmin = $derived(Math.min(...step.top.map((x) => x[2])));
	const lmax = $derived(Math.max(...step.top.map((x) => x[2])));
	const clean = (s) => JSON.stringify(s).slice(1, -1);

	let sampled = $state(null);
	function sample() {
		let r = Math.random();
		for (const p of probs) {
			if ((r -= p.p) <= 0) return (sampled = p.id);
		}
		sampled = probs[probs.length - 1].id;
	}
	$effect(() => {
		ui.step;
		ui.exampleId;
		sampled = null;
	});
</script>

<div class="wrap">
	<div class="chart">
		<div class="hdr hint"><span>token</span><span>logit</span><span>probability at T = {Number(ui.temperature).toFixed(2)}</span></div>
		{#each probs as p, i}
			<div class="row" class:chosen={p.id === step.token_id} class:sampled={p.id === sampled}>
				<span class="tok mono">{clean(p.token)}</span>
				<span class="logit mono">
					<span class="lbar" style="width:{((p.logit - lmin) / (lmax - lmin || 1)) * 100}%"></span>
					<span>{p.logit.toFixed(2)}</span>
				</span>
				<span class="pbar"><span style="width:{p.p * 100}%"></span><em>{(p.p * 100).toFixed(1)}%</em></span>
			</div>
		{/each}
		<p class="hint">Top {probs.length} of {config.text.vocab.toLocaleString()} tokens. Probabilities are renormalized over these {probs.length}.</p>
	</div>

	<div class="side">
		<div class="eq mono">p<sub>i</sub> = exp(z<sub>i</sub> / T) / Σ<sub>j</sub> exp(z<sub>j</sub> / T)</div>
		<p>
			The last hidden state goes through the final RMSNorm and the <code>lm_head</code> ({config.text.hidden} →
			{config.text.vocab.toLocaleString()}), which gives one logit per vocabulary entry. Softmax turns those logits into
			probabilities.
		</p>
		<p>
			<b>Temperature</b> divides the logits before the softmax. Below 1 the distribution sharpens toward the top token; above 1 it
			flattens and unlikely tokens get a real chance. Drag the slider in the header to see it.
		</p>
		<label class="temp">
			<span class="hint">T</span>
			<input type="range" min="0.1" max="2" step="0.05" bind:value={ui.temperature} />
			<span class="mono">{Number(ui.temperature).toFixed(2)}</span>
		</label>
		<p>
			The precomputed run used <b>greedy decoding</b>, which always takes the highest logit (outlined in green), so the text
			doesn't change with T.
		</p>
		<button class="pill" onclick={sample}>🎲 Sample once at this temperature</button>
		{#if sampled !== null}
			<p class="hint">
				Sampled <b class="mono">{clean(probs.find((p) => p.id === sampled).token)}</b>
				{sampled === step.token_id ? '(same as greedy)' : '(the rest of the output would now diverge)'}
			</p>
		{/if}
	</div>
</div>

<style>
	.wrap {
		display: grid;
		grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
		gap: 32px;
		align-items: start;
	}
	.hdr,
	.row {
		display: grid;
		grid-template-columns: 110px 130px 1fr;
		gap: 10px;
		align-items: center;
	}
	.hdr {
		font-size: 11px;
		margin-bottom: 4px;
	}
	.row {
		padding: 2px 6px;
		border-radius: 4px;
		border: 1.5px solid transparent;
	}
	.row.chosen {
		border-color: var(--gen);
	}
	.row.sampled {
		background: var(--accent-soft);
	}
	.tok {
		white-space: pre;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.logit {
		position: relative;
		font-size: 11px;
		height: 16px;
		display: flex;
		align-items: center;
	}
	.lbar {
		position: absolute;
		left: 0;
		top: 3px;
		bottom: 3px;
		background: var(--surface-2);
		border-radius: 2px;
	}
	.logit span:last-child {
		position: relative;
		padding-left: 4px;
	}
	.pbar {
		position: relative;
		height: 16px;
		background: var(--surface-2);
		border-radius: 3px;
		overflow: hidden;
	}
	.pbar span {
		display: block;
		height: 100%;
		background: var(--gen);
		transition: width 0.2s;
	}
	.pbar em {
		position: absolute;
		left: 6px;
		top: 0;
		font-size: 11px;
		font-style: normal;
		line-height: 16px;
	}
	.eq {
		background: var(--surface-2);
		padding: 10px 12px;
		border-radius: 6px;
		font-size: 14px;
	}
	.side p {
		font-size: 14px;
	}
	.temp {
		display: flex;
		gap: 8px;
		align-items: center;
	}
	.temp input {
		flex: 1;
	}
	@media (max-width: 900px) {
		.wrap {
			grid-template-columns: 1fr;
		}
	}
</style>
