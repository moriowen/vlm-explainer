<script>
	import { onDestroy } from 'svelte';
	import { ui } from './state.svelte.js';
	import { dataUrl } from './data.js';

	let { manifest, ex, loading, onselect } = $props();

	let timer;
	function togglePlay() {
		if (ui.playing) return stop();
		if (ui.step >= ex.meta.steps.length - 1) ui.step = 0;
		ui.playing = true;
		timer = setInterval(() => {
			if (ui.step >= ex.meta.steps.length - 1) return stop();
			ui.step += 1;
		}, 700);
	}
	function stop() {
		ui.playing = false;
		clearInterval(timer);
	}
	onDestroy(stop);

	const clean = (s) => s.replace('<end_of_utterance>', '⏎');
</script>

<header>
	<div class="brand">
		<h1>VLM Explainer</h1>
		{#if manifest}
			<a class="model" href="https://huggingface.co/{manifest.config.model_id}" target="_blank" rel="noreferrer">
				{manifest.config.model_id.split('/')[1]}
			</a>
		{/if}
	</div>

	{#if manifest}
		<div class="examples">
			{#each manifest.examples as e (e.id)}
				<button class="ex" class:on={ui.exampleId === e.id} disabled={loading} onclick={() => onselect(e.id)} title={e.title}>
					<img src={dataUrl(`${e.id}/original.jpg`)} alt={e.title} />
				</button>
			{/each}
		</div>
	{/if}

	{#if ex}
		<div class="io card">
			<div class="prompt">
				<span class="label">Prompt</span>
				<span class="ptext">🖼️ {ex.meta.prompt}</span>
			</div>
			<div class="gen">
				<span class="label">Output</span>
				<div class="tokens">
					{#each ex.meta.steps as s, i}
						<button class="tok" class:cur={i === ui.step} class:future={i > ui.step} onclick={() => { stop(); ui.step = i; }}>{clean(s.token)}</button>
					{/each}
				</div>
			</div>
			<div class="controls">
				<button class="pill" onclick={togglePlay}>{ui.playing ? '❚❚ Pause' : '▶ Generate'}</button>
				<input type="range" min="0" max={ex.meta.steps.length - 1} bind:value={ui.step} oninput={stop} aria-label="Generation step" />
				<span class="hint">step {ui.step + 1}/{ex.meta.steps.length}</span>
				<label class="temp">
					<span class="hint">Temperature</span>
					<input type="range" min="0.1" max="2" step="0.05" bind:value={ui.temperature} />
					<span class="mono">{Number(ui.temperature).toFixed(2)}</span>
				</label>
			</div>
		</div>
	{/if}
</header>

<style>
	header {
		display: grid;
		grid-template-columns: auto auto 1fr;
		gap: 16px;
		align-items: center;
		padding: 18px 0;
	}
	.brand h1 {
		font-size: 22px;
		margin: 0;
		letter-spacing: -0.02em;
	}
	.model {
		font-family: var(--mono);
		font-size: 12px;
		color: var(--muted);
		text-decoration: none;
	}
	.examples {
		display: flex;
		gap: 8px;
	}
	.ex {
		width: 54px;
		height: 54px;
		padding: 0;
		border: 2px solid transparent;
		border-radius: 8px;
		overflow: hidden;
		cursor: pointer;
		background: none;
	}
	.ex.on {
		border-color: var(--accent);
	}
	.ex img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		display: block;
	}
	.io {
		padding: 10px 14px;
		display: grid;
		gap: 6px;
		min-width: 0;
	}
	.prompt,
	.gen {
		display: flex;
		gap: 10px;
		align-items: baseline;
		min-width: 0;
	}
	.label {
		font-size: 11px;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--muted);
		width: 52px;
		flex: none;
	}
	.tokens {
		display: flex;
		flex-wrap: wrap;
		min-width: 0;
	}
	.tok {
		border: none;
		background: none;
		padding: 0 1px;
		cursor: pointer;
		white-space: pre;
		border-radius: 3px;
	}
	.tok.future {
		color: var(--muted);
		opacity: 0.35;
	}
	.tok.cur {
		background: var(--gen);
		color: white;
	}
	.controls {
		display: flex;
		gap: 10px;
		align-items: center;
		flex-wrap: wrap;
	}
	.controls > input {
		flex: 1;
		min-width: 120px;
	}
	.temp {
		display: flex;
		gap: 6px;
		align-items: center;
	}
	@media (max-width: 900px) {
		header {
			grid-template-columns: 1fr;
		}
	}
</style>
