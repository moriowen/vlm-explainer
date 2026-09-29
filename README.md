# VLM Explainer

An interactive walkthrough of a vision language model, in the style of [Transformer Explainer](https://poloclub.github.io/transformer-explainer/). It follows [SmolVLM-256M-Instruct](https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct) (Idefics3 architecture) through one forward pass. Every heatmap and number on the page comes from a real run of the model.

The seven stages:

1. **Image processor.** The image is resized, cut into 512px tiles, and a global copy is added. The prompt's `<image>` becomes 64 placeholders per tile.
2. **Patch embedding.** A 16×16 Conv2d turns each tile into 1024 vectors of 768 dims.
3. **Vision encoder.** 12 SigLIP layers. The page shows PCA maps per layer and head-averaged attention.
4. **Connector.** Pixel shuffle stacks each 4×4 patch block into one 12288-d vector, and a linear layer projects it to 576 dims.
5. **Input merger.** Image vectors replace the `<image>` placeholder embeddings.
6. **Language decoder.** 30 Llama layers. The page shows where the current token attends on the image and in the text, plus a logit lens.
7. **Output.** Top-20 next-token probabilities with a temperature slider.

## Running it

```sh
npm install
npm run dev          # http://localhost:5173
npm run build        # static site in build/
```

For a subpath deploy such as GitHub Pages, set `BASE_PATH=/repo-name` when building.

## Regenerating the data

The site reads precomputed activations from `static/data/`. To change the examples, edit `precompute/examples.json` (an image URL or a path relative to `precompute/`, plus a prompt) and run:

```sh
python3 -m venv precompute/.venv
precompute/.venv/bin/pip install torch torchvision transformers pillow accelerate
precompute/.venv/bin/python precompute/extract.py          # all examples
precompute/.venv/bin/python precompute/extract.py cats     # just one
```

It runs on CPU in about a minute per example and writes around 4 to 5 MB per example. Most of that is `vit_attn.bin`.

### Data format (per example)

| File | Contents |
| --- | --- |
| `meta.json` | tokens, tile grid, patch/projection norms, per-step top-20 logits, image-attention share per layer, logit lens |
| `tiles/split_{s}.jpg` | the 512×512 tiles the encoder sees |
| `pca/split_{s}_l{l}.png` | 32×32 PCA→RGB of vision hidden states (`l0` is the patch embedding) |
| `proj/split_{s}.png` | 8×8 PCA→RGB of connector outputs |
| `vit_attn.bin` | uint8 `[layer][split][64 query blocks][1024 keys]`, head-averaged, row-max normalized |
| `dec_attn.bin` | uint8, per generation step `[layer][seq_len]` last-token attention, head-averaged, stored as `sqrt(a / max)` |

Generation is greedy. The temperature slider rescales the stored top-20 logits and does not re-run the model.
