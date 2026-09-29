export const ui = $state({
	exampleId: null,
	split: 0, // selected image split (defaults to the global view on load)
	vitLayer: 6, // 0 = patch embedding, 1..12 = encoder layer outputs
	query: null, // 8x8 query group in the selected split, or null
	step: 0, // generation step
	decLayer: -1, // -1 = average over layers
	temperature: 1,
	stage: 'image', // focused stage in the detail panel
	playing: false
});

export const STAGES = [
	{ id: 'image', name: 'Image Processor', short: 'Split' },
	{ id: 'patch', name: 'Patch Embedding', short: 'Patchify' },
	{ id: 'vit', name: 'Vision Encoder', short: 'ViT ×12' },
	{ id: 'connector', name: 'Connector', short: 'Shuffle + Project' },
	{ id: 'merge', name: 'Input Merger', short: 'Merge' },
	{ id: 'decoder', name: 'Language Decoder', short: 'LLM ×30' },
	{ id: 'output', name: 'Output', short: 'Next token' }
];
