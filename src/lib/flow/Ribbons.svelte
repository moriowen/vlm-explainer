<script>
	import { flow, ui } from '../state.svelte.js';

	/**
	 * bands: [{ id, from, to, key, stage, c1, c2, kind? }]
	 *   from/to are data-rib ids inside `root`. kind 'loop' draws the autoregressive feedback arrow.
	 * version: bump to force re-measuring.
	 */
	let { root, bands, version = 0, onpick = null } = $props();

	let w = $state(0);
	let h = $state(0);
	let paths = $state([]);

	function rectOf(id, box) {
		const el = root?.querySelector(`[data-rib="${id}"]`);
		if (!el) return null;
		const r = el.getBoundingClientRect();
		if (!r.width && !r.height) return null;
		return { l: r.left - box.left, r: r.right - box.left, t: r.top - box.top, b: r.bottom - box.top };
	}

	function ribbon(s, e) {
		const c = Math.max(24, (e.l - s.r) * 0.5);
		return `M${s.r},${s.t} C${s.r + c},${s.t} ${e.l - c},${e.t} ${e.l},${e.t} L${e.l},${e.b} C${e.l - c},${e.b} ${s.r + c},${s.b} ${s.r},${s.b} Z`;
	}

	function loop(s, e, bottom) {
		// from bottom-centre of the source, under the diagram, back up into the target's bottom
		const sx = (s.l + s.r) / 2;
		const ex = (e.l + e.r) / 2;
		const y = bottom - 14;
		const r = 18;
		return `M${sx},${s.b} L${sx},${y - r} Q${sx},${y} ${sx - r},${y} L${ex + r},${y} Q${ex},${y} ${ex},${y - r} L${ex},${e.b + 4}`;
	}

	function measure() {
		if (!root) return;
		const box = root.getBoundingClientRect();
		w = root.scrollWidth;
		h = root.scrollHeight;
		const out = [];
		bands.forEach((b, i) => {
			const s = rectOf(b.from, box);
			const e = rectOf(b.to, box);
			if (!s || !e) return;
			if (b.kind === 'loop') out.push({ ...b, i, d: loop(s, e, h), sx: s.l, tx: e.r });
			else out.push({ ...b, i, d: ribbon(s, e), sx: s.r, tx: e.l });
		});
		paths = out;
	}

	$effect(() => {
		version;
		bands;
		root;
		requestAnimationFrame(measure);
	});

	$effect(() => {
		if (!root) return;
		const ro = new ResizeObserver(() => requestAnimationFrame(measure));
		ro.observe(root);
		const onload = () => requestAnimationFrame(measure);
		root.addEventListener('load', onload, true);
		window.addEventListener('resize', onload);
		return () => {
			ro.disconnect();
			root.removeEventListener('load', onload, true);
			window.removeEventListener('resize', onload);
		};
	});

	const bandState = (p) => {
		if (flow.running === p.stage) return 'grow';
		if (flow.lit >= p.stage) return 'lit';
		return 'ghost';
	};
	const opacity = (p, st) => {
		if (st === 'ghost') return 0.14;
		if (ui.hover) return p.key === ui.hover || p.key === 'all' ? 0.95 : 0.1;
		return p.cached ? 0.35 : 0.72;
	};
</script>

<svg class="ribbons" width={w} height={h} aria-hidden="true">
	<defs>
		{#each paths as p (p.i)}
			<linearGradient id="rg-{p.i}" gradientUnits="userSpaceOnUse" x1={p.sx} x2={p.tx} y1="0" y2="0">
				<stop offset="0" stop-color={p.c1} />
				<stop offset="1" stop-color={p.c2} />
			</linearGradient>
			{#if flow.running === p.stage}
				{@const t = flow.t}
				<linearGradient id="rgg-{p.i}" gradientUnits="userSpaceOnUse" x1={p.sx} x2={p.tx} y1="0" y2="0">
					<stop offset="0" stop-color={p.c1} stop-opacity="0.75" />
					<stop offset={Math.max(0, t - 0.12)} stop-color={p.c2} stop-opacity="0.8" />
					<stop offset={Math.max(0, t - 0.01)} stop-color={p.strong ?? p.c2} stop-opacity="1" />
					<stop offset={t} stop-color={p.strong ?? p.c2} stop-opacity="0" />
					<stop offset="1" stop-color={p.c2} stop-opacity="0" />
				</linearGradient>
			{/if}
		{/each}
		<marker id="loop-head" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
			<path d="M0,0 L10,5 L0,10 z" fill="#25a36a" />
		</marker>
	</defs>
	{#each paths as p (p.i)}
		{@const st = bandState(p)}
		{#if p.kind === 'loop'}
			<path
				d={p.d}
				class="loop"
				class:grow={st === 'grow'}
				style="opacity:{st === 'ghost' ? 0.15 : 1};stroke-dashoffset:{st === 'grow' ? (1 - flow.t) * 60 : 0}"
				marker-end="url(#loop-head)"
			/>
		{:else}
			{#if st === 'grow'}
				<path d={p.d} fill={p.c1} style="opacity:0.1" />
			{/if}
			<path
				d={p.d}
				fill={st === 'grow' ? `url(#rgg-${p.i})` : `url(#rg-${p.i})`}
				style="opacity:{st === 'grow' ? 1 : opacity(p, st)}"
				class="band"
				role="presentation"
				onpointerenter={() => p.key && (ui.hover = p.key)}
				onpointerleave={() => (ui.hover = null)}
				onclick={() => onpick?.(p)}
			/>
		{/if}
	{/each}
</svg>

<style>
	.ribbons {
		position: absolute;
		left: 0;
		top: 0;
		pointer-events: none;
		overflow: visible;
	}
	.band {
		pointer-events: visiblePainted;
		cursor: pointer;
		transition: opacity 0.18s;
	}
	.loop {
		fill: none;
		stroke: #25a36a;
		stroke-width: 2;
		stroke-dasharray: 5 5;
		transition: opacity 0.2s;
	}
</style>
