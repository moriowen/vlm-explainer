<script>
	import { onMount, tick } from 'svelte';
	import '../app.css';
	import { loadManifest, loadExample } from '$lib/data.js';
	import { ui, flow } from '$lib/state.svelte.js';
	import { runFlow, stopFlow } from '$lib/flow/animate.js';
	import Topbar from '$lib/Topbar.svelte';
	import Flow from '$lib/flow/Flow.svelte';
	import Popover from '$lib/Popover.svelte';
	import Article from '$lib/Article.svelte';

	let manifest = $state(null);
	let ex = $state(null);
	let loading = $state(false);
	let error = $state(null);
	let autoplay = $state(false);

	async function select(id) {
		if (id === ui.exampleId) return;
		loading = true;
		error = null;
		autoplay = false;
		stopFlow();
		try {
			const next = await loadExample(id);
			ui.exampleId = id;
			ui.split = next.meta.n_splits - 1;
			ui.query = null;
			ui.step = 0;
			ex = next;
			await tick();
			runFlow(0, 7);
		} catch (e) {
			error = `Could not load example "${id}": ${e.message}`;
		} finally {
			loading = false;
		}
	}

	/** Advance one token: the image is already encoded, so only the decoder side animates. */
	async function generate() {
		if (flow.running >= 0 || !ex) return false;
		const last = ex.meta.steps.length - 1;
		if (ui.step >= last && flow.lit >= 7) {
			ui.step = 0;
			return runFlow(0, 7);
		}
		if (flow.lit < 7) return runFlow(Math.max(0, flow.lit + 1), 7);
		ui.step += 1;
		return runFlow(5, 7, { stageMs: 420 });
	}

	async function toggleAutoplay() {
		autoplay = !autoplay;
		while (autoplay && ex && !(ui.step >= ex.meta.steps.length - 1 && flow.lit >= 7)) {
			if (flow.running >= 0) {
				await new Promise((r) => setTimeout(r, 100));
				continue;
			}
			const ok = await generate();
			if (!ok) break;
			await new Promise((r) => setTimeout(r, 120));
		}
		autoplay = false;
	}

	onMount(async () => {
		try {
			manifest = await loadManifest();
			await select(manifest.examples[0].id);
		} catch (e) {
			error = 'Could not load data/manifest.json. Run precompute/extract.py first.';
		}
	});
</script>

<svelte:head>
	<title>VLM Explainer</title>
	<meta name="description" content="An interactive visual walkthrough of how a vision language model reads an image and answers a question." />
</svelte:head>

<main>
	<Topbar {manifest} {ex} {loading} {autoplay} onselect={select} onjump={(i) => { autoplay = false; stopFlow(); ui.step = i; }} ongenerate={generate} onreplay={() => runFlow(0, 7)} onautoplay={toggleAutoplay} />
	{#if error}
		<p class="error">{error}</p>
	{:else if ex && manifest}
		<Flow {ex} config={manifest.config} />
		<p class="hint tips">
			Hover a tile or a ribbon to trace it through the model · click any column title or ribbon for the details · step through
			layers with ‹ ›
		</p>
		<Popover {ex} config={manifest.config} />
		<Article config={manifest.config} />
	{:else}
		<p class="loading">Loading activations…</p>
	{/if}
</main>

<style>
	main {
		max-width: 1560px;
		margin: 0 auto;
		padding: 0 16px 80px;
	}
	.error,
	.loading {
		padding: 40px 0;
		color: var(--muted);
	}
	.error {
		color: var(--danger);
	}
	.tips {
		text-align: center;
		margin: 4px 0 0;
	}
</style>
