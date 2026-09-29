<script>
	import { paintHeat } from './heat.js';

	/**
	 * A square image with optional heatmap overlay and grid.
	 * heat: Float32Array/array of side*side in [0,1]
	 * hoverSide: grid size used for hover/click cell reporting
	 */
	let {
		src,
		size = 256,
		heat = null,
		heatSide = 32,
		gridSide = 0,
		hoverSide = 0,
		selected = null,
		pixelated = false,
		dim = false,
		onhover = null,
		onpick = null,
		label = ''
	} = $props();

	let canvas = $state();
	let hover = $state(null);

	$effect(() => {
		paintHeat(canvas, heat, heatSide);
	});

	function cellAt(e) {
		const r = e.currentTarget.getBoundingClientRect();
		const x = Math.floor(((e.clientX - r.left) / r.width) * hoverSide);
		const y = Math.floor(((e.clientY - r.top) / r.height) * hoverSide);
		return Math.max(0, Math.min(hoverSide - 1, y)) * hoverSide + Math.max(0, Math.min(hoverSide - 1, x));
	}
	const cellBox = (i, side) => ({
		left: `${((i % side) / side) * 100}%`,
		top: `${(Math.floor(i / side) / side) * 100}%`,
		width: `${100 / side}%`,
		height: `${100 / side}%`
	});
</script>

<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
<div
	class="tile"
	style="width:{size}px;height:{size}px"
	role="img"
	aria-label={label}
	onpointermove={hoverSide ? (e) => { hover = cellAt(e); onhover?.(hover); } : undefined}
	onpointerleave={hoverSide ? () => { hover = null; onhover?.(null); } : undefined}
	onclick={hoverSide && onpick ? (e) => onpick(cellAt(e)) : undefined}
>
	<img {src} alt={label} class:pixelated class:dim draggable="false" />
	<canvas bind:this={canvas} width="256" height="256"></canvas>
	{#if gridSide}
		<div class="grid" style="background-size:{100 / gridSide}% {100 / gridSide}%"></div>
	{/if}
	{#if hoverSide && hover !== null}
		<div class="cell hover" style:left={cellBox(hover, hoverSide).left} style:top={cellBox(hover, hoverSide).top} style:width={cellBox(hover, hoverSide).width} style:height={cellBox(hover, hoverSide).height}></div>
	{/if}
	{#if hoverSide && selected !== null}
		<div class="cell sel" style:left={cellBox(selected, hoverSide).left} style:top={cellBox(selected, hoverSide).top} style:width={cellBox(selected, hoverSide).width} style:height={cellBox(selected, hoverSide).height}></div>
	{/if}
</div>

<style>
	.tile {
		position: relative;
		border-radius: 6px;
		overflow: hidden;
		flex: none;
		max-width: 100%;
		aspect-ratio: 1;
		height: auto !important;
		background: var(--surface-2);
		cursor: crosshair;
		touch-action: none;
	}
	img,
	canvas,
	.grid {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
	}
	img {
		object-fit: cover;
		user-select: none;
	}
	img.pixelated {
		image-rendering: pixelated;
	}
	img.dim {
		filter: grayscale(0.6) brightness(0.55);
	}
	canvas {
		pointer-events: none;
		image-rendering: pixelated;
	}
	.grid {
		pointer-events: none;
		background-image: linear-gradient(to right, rgba(255, 255, 255, 0.25) 1px, transparent 1px),
			linear-gradient(to bottom, rgba(255, 255, 255, 0.25) 1px, transparent 1px);
	}
	.cell {
		position: absolute;
		pointer-events: none;
		box-sizing: border-box;
	}
	.hover {
		outline: 2px solid rgba(255, 255, 255, 0.9);
	}
	.sel {
		outline: 2px solid var(--accent);
		box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.08);
	}
</style>
