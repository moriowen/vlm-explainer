<script>
	import { onMount } from 'svelte';
	import '../app.css';
	import { loadManifest, loadExample } from '$lib/data.js';
	import { ui } from '$lib/state.svelte.js';
	import Header from '$lib/Header.svelte';
	import Pipeline from '$lib/Pipeline.svelte';
	import Detail from '$lib/Detail.svelte';
	import Article from '$lib/Article.svelte';

	let manifest = $state(null);
	let ex = $state(null);
	let loading = $state(false);
	let error = $state(null);

	async function select(id) {
		loading = true;
		error = null;
		try {
			const next = await loadExample(id);
			ui.exampleId = id;
			ui.split = next.meta.n_splits - 1;
			ui.query = null;
			ui.step = 0;
			ex = next;
		} catch (e) {
			error = `Could not load example "${id}": ${e.message}`;
		} finally {
			loading = false;
		}
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
</svelte:head>

<main>
	<Header {manifest} {ex} {loading} onselect={select} />
	{#if error}
		<p class="error">{error}</p>
	{:else if ex && manifest}
		<Pipeline {ex} config={manifest.config} />
		<Detail {ex} config={manifest.config} />
		<Article config={manifest.config} />
	{:else}
		<p class="loading">Loading activations…</p>
	{/if}
</main>

<style>
	main {
		max-width: 1440px;
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
</style>
