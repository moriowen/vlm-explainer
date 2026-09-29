<script>
	import { ui, flow } from './state.svelte.js';
	import { dataUrl } from './data.js';

	let { manifest, ex, loading, onselect, onjump, ongenerate, onreplay, onautoplay, autoplay } = $props();

	const steps = $derived(ex?.meta.steps ?? []);
	const done = $derived(ui.step >= steps.length - 1 && flow.lit >= 7);
	const busy = $derived(flow.running >= 0);
	const clean = (s) => s.replace('<end_of_utterance>', '').replace('\n', ' ');
</script>

<header>
	<div class="brand">
		<div class="logo" aria-hidden="true"><i></i><i></i><i></i><i></i></div>
		<div>
			<h1>VLM Explainer</h1>
			{#if manifest}<a href="https://huggingface.co/{manifest.config.model_id}" target="_blank" rel="noreferrer">{manifest.config.model_id.split('/')[1]}</a>{/if}
		</div>
	</div>

	{#if manifest && ex}
		<div class="input">
			<div class="thumbs" role="radiogroup" aria-label="Example">
				{#each manifest.examples as e (e.id)}
					<button role="radio" aria-checked={ui.exampleId === e.id} class:on={ui.exampleId === e.id} disabled={loading} onclick={() => onselect(e.id)} title={e.title}>
						<img src={dataUrl(`${e.id}/original.jpg`)} alt={e.title} />
					</button>
				{/each}
			</div>
			<div class="textbox">
				<span class="p">{ex.meta.prompt}</span>
				<span class="arrow">→</span>
				<span class="gen">
					{#each steps as s, i}
						{#if i < ui.step || (i === ui.step && flow.lit >= 7)}
							<button class="tok" class:last={i === ui.step} onclick={() => onjump(i)}>{clean(s.token)}</button>
						{/if}
					{/each}
					{#if !done}<span class="caret"></span>{/if}
				</span>
			</div>
			<button class="primary" onclick={ongenerate} disabled={busy || loading}>
				{done ? '↺ Restart' : 'Generate next token'}
			</button>
			<button class="ghost" onclick={onautoplay} disabled={loading} title="Generate the whole answer">{autoplay ? '❚❚' : '▶▶'}</button>
		</div>

		<div class="right">
			<label class="temp">
				<span>Temperature</span>
				<input type="range" min="0.1" max="2" step="0.05" bind:value={ui.temperature} />
				<b>{Number(ui.temperature).toFixed(2)}</b>
			</label>
			<button class="ghost small" onclick={onreplay} disabled={busy} title="Replay the full forward pass from the image">Replay from image</button>
		</div>
	{/if}
</header>

<style>
	header {
		position: sticky;
		top: 0;
		z-index: 50;
		display: flex;
		align-items: center;
		gap: 20px;
		padding: 10px 20px;
		margin: 0 -16px 18px;
		background: color-mix(in srgb, var(--bg) 88%, transparent);
		backdrop-filter: blur(10px);
		border-bottom: 1px solid var(--border);
	}
	.brand {
		display: flex;
		gap: 10px;
		align-items: center;
		flex: none;
	}
	.logo {
		width: 30px;
		height: 30px;
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 3px;
		padding: 4px;
		border-radius: 8px;
		background: linear-gradient(135deg, #ec7a4b, #7c5ce0);
	}
	.logo i {
		background: white;
		border-radius: 2px;
		opacity: 0.9;
	}
	.logo i:nth-child(2),
	.logo i:nth-child(3) {
		opacity: 0.55;
	}
	h1 {
		font-size: 17px;
		margin: 0;
		letter-spacing: -0.02em;
		line-height: 1.1;
	}
	.brand a {
		font-family: var(--mono);
		font-size: 10.5px;
		color: var(--muted);
		text-decoration: none;
	}
	.input {
		flex: 1;
		min-width: 0;
		display: flex;
		align-items: center;
		gap: 8px;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 12px;
		padding: 5px 5px 5px 6px;
		box-shadow: 0 2px 10px rgba(20, 20, 50, 0.06);
	}
	.thumbs {
		display: flex;
		gap: 4px;
		flex: none;
	}
	.thumbs button {
		width: 34px;
		height: 34px;
		padding: 0;
		border-radius: 7px;
		overflow: hidden;
		border: 2px solid transparent;
		cursor: pointer;
		opacity: 0.55;
		transition: opacity 0.15s;
	}
	.thumbs button.on,
	.thumbs button:hover {
		opacity: 1;
	}
	.thumbs button.on {
		border-color: var(--accent);
	}
	.thumbs img {
		width: 100%;
		height: 100%;
		object-fit: cover;
		display: block;
	}
	.textbox {
		flex: 1;
		min-width: 0;
		font-size: 14px;
		display: flex;
		align-items: baseline;
		gap: 6px;
		overflow: hidden;
		white-space: nowrap;
	}
	.p {
		color: var(--text);
		flex: none;
	}
	.arrow {
		color: var(--muted);
	}
	.gen {
		display: flex;
		overflow: hidden;
		align-items: baseline;
		min-width: 0;
	}
	.tok {
		border: none;
		background: none;
		padding: 0;
		white-space: pre;
		color: var(--out);
		cursor: pointer;
		font-size: 14px;
	}
	.tok.last {
		background: var(--out);
		color: white;
		border-radius: 3px;
		animation: pop 0.35s ease-out;
	}
	@keyframes pop {
		from {
			transform: scale(1.3);
		}
	}
	.caret {
		width: 2px;
		height: 16px;
		background: var(--out);
		margin-left: 2px;
		align-self: center;
		animation: blink 1s steps(1) infinite;
	}
	@keyframes blink {
		50% {
			opacity: 0;
		}
	}
	.primary {
		flex: none;
		background: var(--accent);
		color: white;
		border: none;
		border-radius: 8px;
		padding: 8px 14px;
		font-weight: 600;
		font-size: 13px;
		cursor: pointer;
		box-shadow: 0 2px 8px color-mix(in srgb, var(--accent) 40%, transparent);
	}
	.primary:disabled {
		opacity: 0.6;
		cursor: default;
	}
	.ghost {
		flex: none;
		background: var(--surface-2);
		border: 1px solid var(--border);
		border-radius: 8px;
		padding: 7px 10px;
		cursor: pointer;
		font-size: 12px;
	}
	.ghost.small {
		font-size: 11.5px;
	}
	.right {
		display: flex;
		align-items: center;
		gap: 14px;
		flex: none;
	}
	.temp {
		display: flex;
		align-items: center;
		gap: 6px;
		font-size: 12px;
		color: var(--muted);
	}
	.temp input {
		width: 90px;
	}
	.temp b {
		font-family: var(--mono);
		color: var(--text);
		font-weight: 500;
		width: 32px;
	}
	@media (max-width: 1100px) {
		header {
			flex-wrap: wrap;
		}
		.input {
			order: 3;
			flex-basis: 100%;
		}
	}
	@media (max-width: 640px) {
		.textbox .p,
		.textbox .arrow {
			display: none;
		}
		.primary {
			padding: 8px 10px;
		}
	}
</style>
