<script>
	import { ui } from './state.svelte.js';

	let { config } = $props();
	const v = $derived(config.vision);
	const t = $derived(config.text);
	const sf = $derived(config.scale_factor);
	const open = (id) => {
		ui.stage = id;
		window.scrollTo({ top: 0, behavior: 'smooth' });
	};
</script>

<article>
	<h2>How a vision language model reads an image</h2>
	<p>
		A vision language model (VLM) takes an image and some text and writes text back. This page follows
		<a href="https://huggingface.co/{config.model_id}" target="_blank" rel="noreferrer">SmolVLM-256M-Instruct</a> through
		one forward pass. Everything shown above is a real activation, recorded while the model answered the prompt. The model
		is small enough to inspect in full, and it uses the same Idefics3 layout as its larger siblings: a vision encoder turns
		the image into vectors, a connector squeezes those vectors into something the language model can read, and a normal
		decoder-only language model does the rest.
	</p>
	<p>
		The language model never gets pixels. It gets a sequence of vectors, and some of those vectors happen to come from an
		image. Most of the pipeline exists to make that possible.
	</p>

	<h3><button onclick={() => open('image')}>1. Image processor</button></h3>
	<p>
		The vision encoder only accepts 512×512 inputs. A single 512px image would lose most of the detail in a large photo, so
		the processor resizes the image (longest edge {config.longest_edge} here) and cuts it into a grid of 512px tiles. It also
		adds one downscaled copy of the whole image, so the model gets both close-up detail and the overall layout.
	</p>
	<p>
		The prompt changes too. The chat template holds one <code>&lt;image&gt;</code> placeholder, and the processor replaces it
		with 64 placeholders per tile. Each group starts with a tag such as <code>&lt;row_1_col_2&gt;</code> or
		<code>&lt;global-img&gt;</code>, which gives the language model the only clue it has about where a tile sits in the
		original picture.
	</p>

	<h3><button onclick={() => open('patch')}>2. Patch embedding</button></h3>
	<p>
		Each tile is cut into 16×16 pixel patches, a 32×32 grid of 1024 patches. A convolution with kernel size and stride 16
		flattens every patch (16 × 16 × 3 = 768 numbers) and maps it to a {v.hidden}-dimensional vector. A learned position
		embedding is added so the encoder knows where each patch came from. From here on the model works with 1024 vectors per
		tile, not pixels.
	</p>

	<h3><button onclick={() => open('vit')}>3. Vision encoder</button></h3>
	<p>
		The encoder is a SigLIP-style Vision Transformer with {v.layers} layers. Each layer runs self-attention ({v.heads} heads),
		where every patch can look at every other patch in the same tile, and then an MLP applied to each patch on its own. The
		attention is bidirectional, like BERT: there is no causal mask, because an image has no reading order.
	</p>
	<p>
		The PCA view shows what this does. After the patch embedding, colors follow local texture and brightness. A few layers
		later, patches on the same object share a color even when they look different up close. The encoder has mixed in
		context, so each vector now describes part of an object rather than a small square of pixels. The last layer's map is
		harder to read because a few patches stand out sharply and take over the principal components.
	</p>

	<h3><button onclick={() => open('connector')}>4. Connector: pixel shuffle and projection</button></h3>
	<p>
		1024 vectors per tile would be expensive for the language model. Five tiles would already cost over 5000 tokens before
		the question is even read. The connector handles this in two steps.
	</p>
	<p>
		<b>Pixel shuffle</b> takes each {sf}×{sf} block of neighbouring patches and concatenates their vectors into one. That
		gives {sf * sf}× fewer tokens (1024 → {1024 / (sf * sf)}), each {sf * sf}× wider ({v.hidden} → {v.hidden * sf * sf}). No
		information is lost; it only moves from the sequence dimension into the feature dimension. Then a single
		<b>linear projection</b> maps each {v.hidden * sf * sf}-dim vector to {t.hidden} dims, the width of the language
		model's word embeddings. That one matrix is the whole bridge between the two models.
	</p>

	<h3><button onclick={() => open('merge')}>5. Input merger</button></h3>
	<p>
		The prompt, with its image placeholders, goes through the language model's usual embedding table. Then every
		<code>&lt;image&gt;</code> position is overwritten, in order, with one connector output. Nothing here is learned. After
		the merge the sequence is a single <span class="shape">[length, {t.hidden}]</span> matrix, and the decoder treats
		image tokens like any other token.
	</p>

	<h3><button onclick={() => open('decoder')}>6. Language decoder</button></h3>
	<p>
		The decoder is a {t.layers}-layer Llama-style model (SmolLM2). Attention is causal: each position can only see
		earlier positions, which is what lets the model generate one token at a time. It uses {t.heads} query heads that share
		{t.kv_heads} key/value heads (grouped-query attention) and rotary position embeddings. The MLP is a SwiGLU block that
		widens to {t.mlp} dims.
	</p>
	<p>
		The decoder view shows where the newest position looks while it predicts the next word. Pick a token that names
		something in the picture, like "cats" or "insect". In these examples those tokens put more of their attention on the
		image than filler words do, and the share peaks around layers 22 to 24. Layer 1 also sends a large share to the image
		for almost every token, which looks like attention spread evenly rather than aimed at anything. The logit lens decodes
		each layer's hidden state as if it were the last one. Early layers mostly guess punctuation and common words, and content
		words like "cats" usually become the top guess only in the last six or seven layers.
	</p>

	<h3><button onclick={() => open('output')}>7. Output</button></h3>
	<p>
		The last hidden state goes through a final RMSNorm and the <code>lm_head</code>, a {t.hidden} × {t.vocab.toLocaleString()}
		matrix that gives one score (logit) per vocabulary token. Softmax turns the scores into probabilities. The chosen token
		is appended to the sequence and the whole decoder runs again, until the model emits
		<code>&lt;end_of_utterance&gt;</code>. The image is encoded only once; every later step reuses the same image tokens.
	</p>

	<h3>About this page</h3>
	<p class="hint">
		Activations were precomputed with <code>precompute/extract.py</code> using Hugging Face <code>transformers</code>,
		greedy decoding, and eager attention. Attention maps are averaged over heads. Vision attention is also averaged over
		each 4×4 query block. PCA colors are fitted jointly across all tiles of one layer, so colors can be compared between
		tiles but not between layers. Inspired by
		<a href="https://poloclub.github.io/transformer-explainer/" target="_blank" rel="noreferrer">Transformer Explainer</a>
		and the Hugging Face post
		<a href="https://huggingface.co/blog/not-lain/vlms" target="_blank" rel="noreferrer">Visualizing How VLMs Work</a>.
	</p>
</article>

<style>
	article {
		max-width: 760px;
		margin: 56px auto 0;
		font-size: 16px;
		line-height: 1.65;
	}
	h2 {
		font-size: 26px;
		letter-spacing: -0.02em;
	}
	h3 {
		margin: 32px 0 6px;
		font-size: 18px;
	}
	h3 button {
		background: none;
		border: none;
		padding: 0;
		font-weight: inherit;
		cursor: pointer;
		text-align: left;
	}
	h3 button:hover {
		color: var(--accent);
	}
	a {
		color: var(--accent);
	}
</style>
