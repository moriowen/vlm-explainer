<script>
	import { ui } from './state.svelte.js';
	import Detail from './Detail.svelte';

	let { ex, config } = $props();

	function onkey(e) {
		if (e.key === 'Escape') ui.popover = false;
	}
</script>

<svelte:window onkeydown={onkey} />

{#if ui.popover}
	<div class="backdrop" role="presentation" onclick={() => (ui.popover = false)}></div>
	<div class="panel" role="dialog" aria-modal="true" aria-label="Stage details">
		<button class="close" onclick={() => (ui.popover = false)} aria-label="Close">✕</button>
		<Detail {ex} {config} />
	</div>
{/if}

<style>
	.backdrop {
		position: fixed;
		inset: 0;
		z-index: 90;
		background: rgba(18, 18, 30, 0.35);
		backdrop-filter: blur(3px);
		animation: fade 0.18s ease-out;
	}
	.panel {
		position: fixed;
		z-index: 91;
		left: 50%;
		top: 76px;
		transform: translateX(-50%);
		width: min(1240px, calc(100vw - 32px));
		max-height: calc(100vh - 100px);
		overflow: auto;
		border-radius: 14px;
		box-shadow: 0 24px 80px rgba(10, 10, 40, 0.35);
		animation: rise 0.22s cubic-bezier(0.2, 0.8, 0.2, 1);
	}
	.panel :global(.detail .bar) {
		padding-right: 44px;
	}
	.panel :global(.detail) {
		margin: 0;
		border: none;
	}
	.close {
		position: absolute;
		right: 14px;
		top: 14px;
		z-index: 2;
		width: 30px;
		height: 30px;
		border-radius: 50%;
		border: 1px solid var(--border);
		background: var(--surface);
		cursor: pointer;
	}
	@keyframes fade {
		from {
			opacity: 0;
		}
	}
	@keyframes rise {
		from {
			opacity: 0;
			transform: translate(-50%, 16px);
		}
	}
</style>
