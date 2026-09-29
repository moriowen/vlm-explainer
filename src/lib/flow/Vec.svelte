<script>
	import { vecColor } from '../heat.js';

	/** A pooled embedding vector drawn as a strip of diverging colors. */
	let { values, height = 10, rib = undefined, title = '' } = $props();
	let canvas = $state();

	$effect(() => {
		if (!canvas || !values) return;
		const ctx = canvas.getContext('2d');
		values.forEach((v, i) => {
			ctx.fillStyle = vecColor(v);
			ctx.fillRect(i, 0, 1, 1);
		});
	});
</script>

<canvas bind:this={canvas} width={values?.length ?? 48} height="1" style="height:{height}px" data-rib={rib} {title}></canvas>

<style>
	canvas {
		display: block;
		width: 100%;
		image-rendering: pixelated;
		border-radius: 2px;
	}
</style>
