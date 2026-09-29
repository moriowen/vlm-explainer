"""Run SmolVLM-256M-Instruct on preset examples and dump activations for the visualizer.

Output layout (per example, under ../static/data/<id>/):
  meta.json                   config, tokens, generation, per-step top-k, logit lens, offsets
  tiles/split_{s}.jpg         the 512x512 splits the vision encoder sees (de-normalized)
  pca/split_{s}_l{l}.png      32x32 PCA->RGB of vision hidden states (l=0 is patch embedding)
  proj/split_{s}.png          8x8 PCA->RGB of connector output tokens
  vit_attn.bin                uint8 [layer][split][64 query groups][1024 keys], head-avg, row-max normalized
  dec_attn.bin                uint8, per step then per layer: last-token attention over the sequence
"""

import io
import json
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from transformers import AutoModelForImageTextToText, AutoProcessor

MODEL_ID = "HuggingFaceTB/SmolVLM-256M-Instruct"
OUT = Path(__file__).resolve().parent.parent / "static" / "data"
LONGEST_EDGE = 1024  # 2x2 grid + global = 5 splits for square-ish images
MAX_NEW_TOKENS = 32
TOP_K = 20
LENS_K = 5

EXAMPLES = json.loads((Path(__file__).parent / "examples.json").read_text())

torch.manual_seed(0)


def load_image(src: str) -> Image.Image:
    if src.startswith("http"):
        req = urllib.request.Request(src, headers={"User-Agent": "vlm-viz/0.1"})
        data = urllib.request.urlopen(req, timeout=60).read()
        return Image.open(io.BytesIO(data)).convert("RGB")
    return Image.open(Path(__file__).parent / src).convert("RGB")


def pca_rgb(x: torch.Tensor) -> np.ndarray:
    """x: [N, D] -> [N, 3] uint8, using joint PCA with percentile scaling."""
    x = x.float() - x.float().mean(0, keepdim=True)
    _, _, v = torch.pca_lowrank(x, q=3, center=False)
    p = (x @ v[:, :3]).numpy()
    lo, hi = np.percentile(p, 2, axis=0), np.percentile(p, 98, axis=0)
    p = np.clip((p - lo) / (hi - lo + 1e-8), 0, 1)
    return (p * 255).astype(np.uint8)


def save_grid_png(rgb: np.ndarray, side: int, path: Path):
    Image.fromarray(rgb.reshape(side, side, 3)).save(path)


def tok_str(tokenizer, i: int) -> str:
    return tokenizer.decode([i])


def main(only=None):
    proc = AutoProcessor.from_pretrained(MODEL_ID)
    proc.image_processor.size = {"longest_edge": LONGEST_EDGE}
    model = AutoModelForImageTextToText.from_pretrained(
        MODEL_ID, dtype=torch.float32, attn_implementation="eager"
    ).eval()
    tok = proc.tokenizer
    vcfg, tcfg = model.config.vision_config, model.config.text_config
    scale = model.config.scale_factor
    image_token_id = model.config.image_token_id

    for ex in EXAMPLES:
        if only and ex["id"] not in only:
            continue
        print(f"== {ex['id']}")
        d = OUT / ex["id"]
        for sub in ("tiles", "pca", "proj"):
            (d / sub).mkdir(parents=True, exist_ok=True)

        img = load_image(ex["image"])
        img.thumbnail((1024, 1024))
        img.save(d / "original.jpg", quality=88)

        messages = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": ex["prompt"]}]}]
        text = proc.apply_chat_template(messages, add_generation_prompt=True)
        inputs = proc(text=text, images=[img], return_tensors="pt")
        pv = inputs["pixel_values"][0]  # [splits, 3, 512, 512]
        n_splits = pv.shape[0]
        grid = re.findall(r"<row_(\d+)_col_(\d+)>", proc.tokenizer.decode(inputs["input_ids"][0]))
        rows = max((int(r) for r, _ in grid), default=0)
        cols = max((int(c) for _, c in grid), default=0)

        # ---- tiles (de-normalize) ----
        mean = torch.tensor(proc.image_processor.image_mean).view(3, 1, 1)
        std = torch.tensor(proc.image_processor.image_std).view(3, 1, 1)
        for s in range(n_splits):
            t = (pv[s] * std + mean).clamp(0, 1).permute(1, 2, 0).numpy()
            Image.fromarray((t * 255).astype(np.uint8)).save(d / "tiles" / f"split_{s}.jpg", quality=90)

        with torch.no_grad():
            # ---- vision encoder ----
            vm = model.model.vision_model
            vout = vm(pixel_values=pv, output_attentions=True, output_hidden_states=True)
            hs = vout.hidden_states  # 13 x [splits, 1024, 768]; hs[0] = patch emb + pos emb
            patch_only = vm.embeddings.patch_embedding(pv).flatten(2).transpose(1, 2)  # before pos emb
            vision_layers = [patch_only] + list(hs[1:-1]) + [vout.last_hidden_state]
            side = vcfg.image_size // vcfg.patch_size  # 32
            n_patches = side * side
            for l, h in enumerate(vision_layers):
                rgb = pca_rgb(h.reshape(-1, h.shape[-1])).reshape(n_splits, n_patches, 3)
                for s in range(n_splits):
                    save_grid_png(rgb[s], side, d / "pca" / f"split_{s}_l{l}.png")
            patch_norms = patch_only.norm(dim=-1).reshape(n_splits, side, side)

            # attention: [splits, heads, 1024, 1024] per layer -> head-avg, pool queries into 8x8 groups
            g = side // scale  # 8
            vit = np.zeros((len(vout.attentions), n_splits, g * g, n_patches), dtype=np.uint8)
            vit_attn_entropy = []
            for l, a in enumerate(vout.attentions):
                a = a.mean(1)  # [splits, q, k]
                a = a.reshape(n_splits, g, scale, g, scale, n_patches).mean((2, 4)).reshape(n_splits, g * g, n_patches)
                ent = -(a * (a + 1e-12).log()).sum(-1).mean().item()
                vit_attn_entropy.append(round(ent, 4))
                a = a / a.amax(-1, keepdim=True)
                vit[l] = (a * 255).round().byte().numpy()
            vit.tofile(d / "vit_attn.bin")

            # ---- connector ----
            conn = model.model.connector
            shuffled = conn.pixel_shuffle(vout.last_hidden_state, scale)  # [splits, 64, 12288]
            projected = conn.modality_projection(shuffled)  # [splits, 64, 576]
            prgb = pca_rgb(projected.reshape(-1, projected.shape[-1])).reshape(n_splits, g * g, 3)
            for s in range(n_splits):
                save_grid_png(prgb[s], g, d / "proj" / f"split_{s}.png")
            proj_norms = projected.norm(dim=-1)

            # ---- decoder: greedy generation, full forward each step to capture attentions ----
            ids = inputs["input_ids"]
            prompt_len = ids.shape[1]
            steps = []
            dec_chunks = []
            dec_offsets = []
            offset = 0
            for step in range(MAX_NEW_TOKENS):
                out = model(
                    input_ids=ids,
                    attention_mask=torch.ones_like(ids),
                    pixel_values=inputs["pixel_values"],
                    pixel_attention_mask=inputs.get("pixel_attention_mask"),
                    output_attentions=True,
                    output_hidden_states=True,
                )
                logits = out.logits[0, -1]
                top_v, top_i = logits.topk(TOP_K)
                seq_len = ids.shape[1]
                layer_attn = []
                img_mass = []
                is_img = (ids[0] == image_token_id)
                for a in out.attentions:
                    row = a[0, :, -1, :].mean(0)  # head-avg last-token attention [seq]
                    img_mass.append(round(float(row[is_img].sum()), 4))
                    layer_attn.append(row)
                la = torch.stack(layer_attn)  # [layers, seq]
                # store sqrt-scaled for visibility; client knows the transform
                la_n = (la / la.amax(-1, keepdim=True)).sqrt()
                dec_chunks.append((la_n * 255).round().byte().numpy())
                dec_offsets.append(offset)
                offset += la.numel()

                # logit lens at last position
                lens = []
                for h in out.hidden_states[1:]:
                    ll = model.lm_head(model.model.text_model.norm(h[0, -1]))
                    pv_, pi_ = ll.softmax(-1).topk(LENS_K)
                    lens.append([[tok_str(tok, int(i)), round(float(p), 4)] for i, p in zip(pi_, pv_)])

                next_id = int(top_i[0])
                steps.append({
                    "seq_len": seq_len,
                    "token": tok_str(tok, next_id),
                    "token_id": next_id,
                    "top": [[tok_str(tok, int(i)), int(i), round(float(v), 4)] for i, v in zip(top_i, top_v)],
                    "img_mass": img_mass,
                    "lens": lens,
                })
                print(f"  step {step}: {tok_str(tok, next_id)!r}")
                if next_id in (tok.eos_token_id, tok.convert_tokens_to_ids("<end_of_utterance>")):
                    break
                ids = torch.cat([ids, torch.tensor([[next_id]])], dim=1)
            np.concatenate([c.reshape(-1) for c in dec_chunks]).tofile(d / "dec_attn.bin")

            # merged input embeddings (hidden_states[0]) and final-layer states, pooled to 48 dims for vector stripes
            def pool48(h):
                h = h.reshape(h.shape[0], 48, -1).mean(-1)
                h = h / (h.abs().amax(-1, keepdim=True) + 1e-8)
                return (h * 127).round().int().tolist()
            embed_vecs = pool48(out.hidden_states[0][0])
            final_vecs = pool48(out.hidden_states[-1][0])

        # ---- tokens (full final sequence) ----
        all_ids = ids[0].tolist()
        tokens = []
        img_counter = 0
        per_split = g * g
        for pos, i in enumerate(all_ids):
            t = {"id": i, "s": tok_str(tok, i)}
            if i == image_token_id:
                t["kind"] = "image"
                t["split"] = img_counter // per_split
                t["q"] = img_counter % per_split
                img_counter += 1
            elif pos >= prompt_len:
                t["kind"] = "gen"
            elif t["s"].startswith("<") and t["s"].endswith(">"):
                t["kind"] = "special"
            else:
                t["kind"] = "text"
            tokens.append(t)

        meta = {
            "id": ex["id"],
            "title": ex["title"],
            "prompt": ex["prompt"],
            "chat_text": text,
            "original_size": list(img.size),
            "rows": rows,
            "cols": cols,
            "n_splits": n_splits,
            "prompt_len": prompt_len,
            "tokens": tokens,
            "patch_norms": [[round(float(v), 2) for v in r.flatten()] for r in patch_norms],
            "proj_norms": [[round(float(v), 2) for v in r] for r in proj_norms],
            "vit_attn_entropy": vit_attn_entropy,
            "steps": steps,
            "dec_offsets": dec_offsets,
            "embed_vecs": embed_vecs,
            "final_vecs": final_vecs,
            "output": tok.decode([s["token_id"] for s in steps], skip_special_tokens=True).strip(),
        }
        (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False))
        print("  ->", meta["output"])

    config = {
        "model_id": MODEL_ID,
        "vision": {"layers": vcfg.num_hidden_layers, "heads": vcfg.num_attention_heads, "hidden": vcfg.hidden_size,
                   "mlp": vcfg.intermediate_size, "patch": vcfg.patch_size, "image_size": vcfg.image_size},
        "scale_factor": scale,
        "text": {"layers": tcfg.num_hidden_layers, "heads": tcfg.num_attention_heads, "kv_heads": tcfg.num_key_value_heads,
                 "hidden": tcfg.hidden_size, "mlp": tcfg.intermediate_size, "vocab": tcfg.vocab_size},
        "longest_edge": LONGEST_EDGE,
    }
    manifest = [
        {"id": e["id"], "title": e["title"], "prompt": e["prompt"]}
        for e in EXAMPLES
        if (OUT / e["id"] / "meta.json").exists()
    ]
    (OUT / "manifest.json").write_text(json.dumps({"config": config, "examples": manifest}, indent=2))


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
