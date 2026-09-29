export const ui = $state({
	exampleId: null,
	split: 0, // selected image split (defaults to the global view on load)
	vitLayer: 6, // 0 = patch embedding, 1..12 = encoder layer outputs
	query: null, // 8x8 query group in the selected split, or null
	step: 0, // generation step
	decLayer: -1, // -1 = average over layers
	temperature: 1,
	stage: 'image', // stage shown in the popover
	popover: false,
	hover: null, // ribbon key being traced: 'split-<s>' | 'text' | null
	playing: false
});

/**
 * Flow animation. Stages light up left to right:
 * 0 image→tiles, prompt→tokens · 1 tiles→patches, tokens→embeddings · 2 patches→ViT · 3 ViT→connector
 * 4 connector/embeddings→sequence · 5 sequence→decoder · 6 decoder→output · 7 output→sequence (loop)
 */
export const flow = $state({
	running: -1, // stage currently pulsing, -1 when idle
	t: 0, // pulse position 0..1 within the running stage
	lit: 7, // highest stage that has been reached
	cached: false // vision side reused from the first pass
});

export const LAST_STAGE = 7;

export const STAGES = [
	{ id: 'image', name: 'Image Processor' },
	{ id: 'patch', name: 'Patch Embedding' },
	{ id: 'vit', name: 'Vision Encoder' },
	{ id: 'connector', name: 'Connector' },
	{ id: 'merge', name: 'Input Merger' },
	{ id: 'decoder', name: 'Language Decoder' },
	{ id: 'output', name: 'Output' }
];

export function openStage(id) {
	ui.stage = id;
	ui.popover = true;
}
