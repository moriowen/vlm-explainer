<script>
	import { ui, flow, openStage } from '../state.svelte.js';
	import { dataUrl, vitRow, decRow, decRowAvg, rowToImageGrids, softmaxTemp, segmentsOf } from '../data.js';
	import { splitPair, TEXT, DEC, OUT } from '../heat.js';
	import { reached } from './animate.js';
	import Ribbons from './Ribbons.svelte';
	import Seq from './Seq.svelte';
	import Vec from './Vec.svelte';
	import Tile from '../Tile.svelte';

	let { ex, config } = $props();

	const m = $derived(ex.meta);
	const S = $derived(m.n_splits);
	const step = $derived(m.steps[ui.step]);
	const len = $derived(step.seq_len);
	const segments = $derived(segmentsOf(m, len));
	const v = $derived(config.vision);
	const t = $derived(config.text);

	// Prompt words that come straight from the user (not template tokens).
	const promptToks = $derived.by(() => {
		const lastImg = m.tokens.findLastIndex((x) => x.kind === 'image');
		const out = [];
		for (let p = lastImg + 1; p < m.prompt_len; p++) {
			const x = m.tokens[p];
			if (x.s === '<end_of_utterance>') break;
			if (x.kind === 'text') out.push({ ...x, pos: p });
		}
		return out;
	});

	// ---- decoder attention ----
	const L = $derived(t.layers);
	const attnRow = $derived(ui.decLayer < 0 ? decRowAvg(ex, ui.step, L) : decRow(ex, ui.step, ui.decLayer));
	const grids = $derived(rowToImageGrids(ex, attnRow));
	const imgShare = $derived(
		ui.decLayer < 0 ? step.img_mass.reduce((a, b) => a + b, 0) / L : step.img_mass[ui.decLayer]
	);

	// ---- vision encoder hover attention ----
	let vitHover = $state(null); // { s, q }
	const vitHeat = $derived(
		vitHover && ui.vitLayer > 0 ? vitRow(ex, ui.vitLayer - 1, vitHover.s, vitHover.q) : null
	);

	// ---- output ----
	const probs = $derived(softmaxTemp(step.top, ui.temperature).slice(0, 8));
	const clean = (s) => JSON.stringify(s).slice(1, -1).replace('<end_of_utterance>', '⟨eou⟩');

	// ---- ribbons ----
	const bands = $derived.by(() => {
		const out = [];
		const cachedVision = ui.step > 0;
		for (let s = 0; s < S; s++) {
			const [c, cl] = splitPair(s, S);
			const key = `split-${s}`;
			const base = { key, c1: cl, c2: cl, strong: c };
			out.push({ ...base, from: s === S - 1 ? 'img-whole' : `img-cell-${s}`, to: `tile-${s}`, stage: 0, cached: cachedVision });
			out.push({ ...base, from: `tile-${s}`, to: `patch-${s}`, stage: 1, cached: cachedVision });
			out.push({ ...base, from: `patch-${s}`, to: `vit-${s}`, stage: 2, cached: cachedVision });
			out.push({ ...base, from: `vit-${s}`, to: `proj-${s}`, stage: 3, cached: cachedVision });
			out.push({ ...base, from: `proj-${s}`, to: `seq-img-${s}`, stage: 4, cached: cachedVision });
			out.push({ ...base, from: `seq-img-${s}`, to: `dec-img-${s}`, stage: 5, c2: DEC[1], strong: DEC[0] });
		}
		const tb = { key: 'text', c1: TEXT[1], c2: TEXT[1], strong: TEXT[0] };
		for (const p of promptToks) {
			out.push({ ...tb, from: 'prompt', to: `tok-${p.pos}`, stage: 0 });
			out.push({ ...tb, from: `tok-${p.pos}`, to: `emb-${p.pos}`, stage: 1 });
			out.push({ ...tb, from: `emb-${p.pos}`, to: `seq-tok-${p.pos}`, stage: 4 });
		}
		segments.forEach((seg, i) => {
			if (seg.type === 'chips') out.push({ ...tb, from: `seq-seg-${i}`, to: `dec-seg-${i}`, stage: 5, c2: DEC[1], strong: DEC[0] });
		});
		out.push({ key: 'all', from: 'dec-next', to: 'out-box', stage: 6, c1: DEC[1], c2: OUT[1], strong: OUT[0] });
		out.push({ key: 'all', from: 'out-box', to: 'seq-next', stage: 7, kind: 'loop' });
		return out;
	});

	let root = $state();
	const version = $derived(`${m.id}-${ui.step}-${ui.decLayer}-${flow.lit >= 6}`);

	// Vision lane geometry
	const gap = $derived(S > 5 ? 6 : 10);
	const tileSize = $derived(S > 6 ? 44 : 60);
	const projSize = $derived(Math.round(tileSize * 0.62));
	const PAD = 44; // space above/below the tile rows, room for the ViT card header
	const VH = $derived(S * tileSize + (S - 1) * gap + 2 * PAD);

	const node = (k) => (reached(k) ? 'on' : 'off');
	const traced = (s) => (ui.hover === null ? '' : ui.hover === `split-${s}` ? 'hl' : 'dim');
	const tracedText = $derived(ui.hover === null ? '' : ui.hover === 'text' ? 'hl' : 'dim');

	const cols = [
		{ id: 'image', title: 'Input', sub: 'image + prompt' },
		{ id: 'image', title: 'Tiles', sub: (S) => `[${S}, 3, 512, 512]` },
		{ id: 'patch', title: 'Patch Embed', sub: (S, v) => `[${S}, 1024, ${v.hidden}]` },
		{ id: 'vit', title: 'Vision Encoder', sub: (S, v) => `${v.layers} layers · [${S}, 1024, ${v.hidden}]` },
		{ id: 'connector', title: 'Connector', sub: (S, v, t) => `[${S}, 64, ${t.hidden}]` },
		{ id: 'merge', title: 'Merged Sequence', sub: (S, v, t, len) => `[${len}, ${t.hidden}]` },
		{ id: 'decoder', title: 'Language Model', sub: (S, v, t) => `${t.layers} layers · causal` },
		{ id: 'output', title: 'Next Token', sub: (S, v, t) => `[${t.vocab.toLocaleString()}]` }
	];
</script>

<div class="scroller">
	<div class="flow" bind:this={root} style="--vh:{VH}px;--gap:{gap}px;--tile:{tileSize}px;--proj:{projSize}px;--pad:{PAD}px">
		<Ribbons {root} {bands} {version} onpick={(p) => openStage(['image', 'patch', 'vit', 'connector', 'merge', 'decoder', 'output', 'output'][p.stage])} />

		<div class="cols">
			{#each cols as c, i}
				<button class="colhead" style="grid-column:{i + 1}" onclick={() => openStage(c.id)} title="Open details">
					<span class="ct">{c.title}</span>
					<span class="cs">{typeof c.sub === 'function' ? c.sub(S, v, t, len) : c.sub}</span>
				</button>
			{/each}

			<!-- 1. input -->
			<div class="col c1 vision">
				<div class="imgwrap" data-rib="img-whole" style="aspect-ratio:{m.original_size[0]}/{m.original_size[1]}">
					<img src={dataUrl(`${m.id}/original.jpg`)} alt="Input" />
					{#each Array(m.rows * m.cols) as _, k}
						<div
							class="cell {traced(k)}"
							data-rib="img-cell-{k}"
							role="presentation"
							style="left:{((k % m.cols) / m.cols) * 100}%;top:{(Math.floor(k / m.cols) / m.rows) * 100}%;width:{100 / m.cols}%;height:{100 / m.rows}%;--c:{splitPair(k, S)[0]}"
							onpointerenter={() => (ui.hover = `split-${k}`)}
							onpointerleave={() => (ui.hover = null)}
						></div>
					{/each}
				</div>
				<p class="note">{m.original_size[0]}×{m.original_size[1]} px, resized to {m.cols * 512}×{m.rows * 512} and cut into {m.rows * m.cols} tiles + 1 global view</p>
			</div>
			<div class="col c1 text">
				<div class="prompt {tracedText}" data-rib="prompt" role="presentation" onpointerenter={() => (ui.hover = 'text')} onpointerleave={() => (ui.hover = null)}>
					<span class="plabel">prompt</span>
					{m.prompt}
				</div>
			</div>

			<!-- 2. tiles / tokens -->
			<div class="col c2 vision rows {node(0)}">
				{#each Array(S) as _, s}
					<div class="row {traced(s)}" role="presentation" onpointerenter={() => (ui.hover = `split-${s}`)} onpointerleave={() => (ui.hover = null)}>
						<img class="tile" data-rib="tile-{s}" src={dataUrl(`${m.id}/tiles/split_${s}.jpg`)} alt="Tile {s + 1}" style="border-color:{splitPair(s, S)[0]}" />
					</div>
				{/each}
			</div>
			<div class="col c2 text {node(0)} {tracedText}">
				<div class="lanelbl">tokens</div>
				{#each promptToks as p}
					<div class="tokrow"><span class="tok" data-rib="tok-{p.pos}" title="token id {p.id}">{p.s}</span></div>
				{/each}
			</div>

			<!-- 3. patch embedding / text embedding -->
			<div class="col c3 vision rows {node(1)}">
				{#each Array(S) as _, s}
					<div class="row {traced(s)}">
						<img class="tile px" data-rib="patch-{s}" src={dataUrl(`${m.id}/pca/split_${s}_l0.png`)} alt="" />
					</div>
				{/each}
			</div>
			<div class="col c3 text {node(1)} {tracedText}">
				<div class="lanelbl">embeddings</div>
				{#each promptToks as p}
					<div class="tokrow"><Vec values={m.embed_vecs?.[p.pos]} rib="emb-{p.pos}" title="{p.s} → {t.hidden}-d vector (pooled to 48)" /></div>
				{/each}
			</div>

			<!-- 4. vision encoder -->
			<div class="col c4 vision {node(2)}">
				<div class="stack">
					<div class="card">
						<div class="cardhead">
							<button class="nav" onclick={() => (ui.vitLayer = Math.max(0, ui.vitLayer - 1))} aria-label="Previous layer">‹</button>
							<span class="lt">{ui.vitLayer === 0 ? 'embed' : `layer ${ui.vitLayer}`}<small> / {v.layers}</small></span>
							<button class="nav" onclick={() => (ui.vitLayer = Math.min(v.layers, ui.vitLayer + 1))} aria-label="Next layer">›</button>
						</div>
						<div class="rows inner">
							{#each Array(S) as _, s}
								<div class="row {traced(s)}">
									<div data-rib="vit-{s}" class="vitmap">
										<Tile
											src={vitHover?.s === s && vitHeat ? dataUrl(`${m.id}/tiles/split_${s}.jpg`) : dataUrl(`${m.id}/pca/split_${s}_l${ui.vitLayer}.png`)}
											size={tileSize}
											pixelated={!(vitHover?.s === s && vitHeat)}
											dim={vitHover?.s === s && !!vitHeat}
											hoverSide={8}
											heat={vitHover?.s === s ? vitHeat : null}
											heatSide={32}
											onhover={(q) => (vitHover = q === null ? null : { s, q })}
											onpick={() => { ui.split = s; openStage('vit'); }}
											label="Vision layer {ui.vitLayer}, tile {s + 1}"
										/>
									</div>
								</div>
							{/each}
						</div>
						<input class="slider" type="range" min="0" max={v.layers} bind:value={ui.vitLayer} aria-label="Vision layer" />
					</div>
				</div>
				{#if ui.step > 0}<span class="cached">↺ cached after token 1</span>{/if}
			</div>
			<div class="col c4 text {node(1)}">
				<p class="skip">text tokens skip the vision side →</p>
			</div>

			<!-- 5. connector -->
			<div class="col c5 vision rows {node(3)}">
				{#each Array(S) as _, s}
					<div class="row {traced(s)}">
						<img class="proj px" data-rib="proj-{s}" src={dataUrl(`${m.id}/proj/split_${s}.png`)} alt="" />
					</div>
				{/each}
				<span class="shrink">1024 → 64<br />per tile</span>
			</div>

			<!-- 6. merged sequence -->
			<div class="col c6 full {node(4)}">
				<Seq {ex} {len} {segments} prefix="seq" pending={reached(7) ? step.token : null} />
			</div>

			<!-- 7. decoder -->
			<div class="col c7 full {node(5)}">
				<div class="stack dec">
					<div class="card">
						<div class="cardhead">
							<button class="nav" onclick={() => (ui.decLayer = Math.max(-1, ui.decLayer - 1))} aria-label="Previous layer">‹</button>
							<span class="lt">{ui.decLayer < 0 ? 'all layers' : `layer ${ui.decLayer + 1}`}<small>{ui.decLayer < 0 ? ' avg' : ` / ${L}`}</small></span>
							<button class="nav" onclick={() => (ui.decLayer = Math.min(L - 1, ui.decLayer + 1))} aria-label="Next layer">›</button>
						</div>
						<div class="spark" role="group" aria-label="Attention on image per layer">
							{#each step.img_mass as mm, l}
								<button class:on={ui.decLayer === l} onclick={() => (ui.decLayer = ui.decLayer === l ? -1 : l)} title="Layer {l + 1}: {(mm * 100).toFixed(0)}% on image" aria-label="Layer {l + 1}">
									<span style="height:{Math.max(6, mm * 100)}%"></span>
								</button>
							{/each}
						</div>
						<div class="share"><b>{(imgShare * 100).toFixed(0)}%</b> of attention on the image</div>
						<Seq {ex} {len} {segments} prefix="dec" mode="attn" row={attnRow} {grids} />
					</div>
				</div>
			</div>

			<!-- 8. output -->
			<div class="col c8 full {node(6)}">
				<div class="outbox" data-rib="out-box">
					<div class="obhead">P(next token) <span>T = {Number(ui.temperature).toFixed(2)}</span></div>
					{#each probs as p}
						<div class="prow" class:chosen={p.id === step.token_id} data-rib={p.id === step.token_id ? 'out-chosen' : undefined}>
							<span class="ptok">{clean(p.token)}</span>
							<span class="pbar"><span style="width:{reached(6) ? p.p * 100 : 0}%"></span></span>
							<span class="pval">{(p.p * 100).toFixed(1)}%</span>
						</div>
					{/each}
					<div class="obfoot">greedy pick → appended to the sequence</div>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.scroller {
		overflow-x: auto;
		overflow-y: hidden;
		margin: 0 -16px;
		padding: 0 16px;
	}
	.flow {
		position: relative;
		min-width: 1340px;
		padding-bottom: 36px;
	}
	.cols {
		position: relative;
		display: grid;
		grid-template-columns: 158px 64px 84px 132px 44px 188px 188px 168px;
		grid-template-rows: auto var(--vh) auto;
		column-gap: 44px;
		row-gap: 26px;
		pointer-events: none;
		justify-content: space-between;
	}
	.cols > * {
		pointer-events: auto;
	}
	.colhead {
		grid-row: 1;
		background: none;
		border: none;
		padding: 0 0 2px;
		text-align: left;
		cursor: pointer;
		display: flex;
		flex-direction: column;
		border-bottom: 2px solid var(--border);
		transition: border-color 0.15s;
	}
	.colhead:hover {
		border-color: var(--accent);
	}
	.ct {
		font-weight: 650;
		font-size: 13px;
		white-space: nowrap;
	}
	.cs {
		font-family: var(--mono);
		font-size: 10px;
		color: var(--muted);
		white-space: nowrap;
	}
	.col {
		transition: opacity 0.35s;
	}
	.col.off {
		opacity: 0.12;
	}
	.vision {
		grid-row: 2;
	}
	.text {
		grid-row: 3;
	}
	.full {
		grid-row: 2 / span 2;
	}
	.c1 {
		grid-column: 1;
	}
	.c2 {
		grid-column: 2;
	}
	.c3 {
		grid-column: 3;
	}
	.c4 {
		grid-column: 4;
	}
	.c5 {
		grid-column: 5;
	}
	.c6 {
		grid-column: 6;
	}
	.c7 {
		grid-column: 7;
	}
	.c8 {
		grid-column: 8;
		display: flex;
		flex-direction: column;
		justify-content: flex-end;
	}
	.rows {
		display: flex;
		flex-direction: column;
		justify-content: center;
		gap: var(--gap);
		height: var(--vh);
	}
	.rows.inner {
		height: auto;
		gap: var(--gap);
	}
	.row {
		height: var(--tile);
		display: flex;
		align-items: center;
		justify-content: center;
		transition: opacity 0.2s;
	}
	.row.dim,
	.dim {
		opacity: 0.25;
	}
	.tile {
		width: var(--tile);
		height: var(--tile);
		border-radius: 5px;
		border: 2px solid transparent;
		object-fit: cover;
		display: block;
		background: var(--surface-2);
	}
	.px {
		image-rendering: pixelated;
	}
	.proj {
		width: var(--proj);
		height: var(--proj);
		border-radius: 3px;
		display: block;
	}
	.imgwrap {
		position: relative;
		width: 100%;
		border-radius: 8px;
		overflow: hidden;
		box-shadow: 0 6px 20px rgba(20, 20, 40, 0.14);
		margin-top: var(--pad);
	}
	.imgwrap img {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	.cell {
		position: absolute;
		border: 1.5px solid var(--c);
		transition: background 0.2s;
	}
	.cell.hl {
		background: color-mix(in srgb, var(--c) 30%, transparent);
		border-width: 3px;
	}
	.note {
		font-size: 11px;
		color: var(--muted);
		margin: 10px 0 0;
		line-height: 1.4;
	}
	.prompt {
		background: var(--surface);
		border: 1.5px solid var(--text-lane);
		border-radius: 8px;
		padding: 8px 10px;
		font-size: 13px;
		box-shadow: 0 4px 14px rgba(20, 20, 60, 0.08);
		margin-top: 18px;
		transition: opacity 0.2s;
	}
	.plabel {
		display: block;
		font-size: 10px;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: var(--muted);
	}
	.lanelbl {
		font-size: 10px;
		color: var(--muted);
		text-transform: uppercase;
		letter-spacing: 0.06em;
		margin-bottom: 4px;
		white-space: nowrap;
	}
	.tokrow {
		height: 20px;
		display: flex;
		align-items: center;
	}
	.tok {
		font-family: var(--mono);
		font-size: 11px;
		background: var(--chip-text);
		border-radius: 3px;
		padding: 0 5px;
		white-space: pre;
		max-width: 100%;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.c3 .tokrow :global(canvas) {
		width: 100%;
	}
	.skip {
		font-size: 11px;
		color: var(--muted);
		margin: 60px 0 0;
		font-style: italic;
	}
	.shrink {
		position: absolute;
		bottom: 4px;
		left: -10px;
		width: 64px;
		font-size: 10px;
		color: var(--muted);
		text-align: center;
		line-height: 1.3;
	}
	.c5 {
		position: relative;
	}
	/* stacked layer cards */
	.stack {
		position: relative;
	}
	.stack::before,
	.stack::after {
		content: '';
		position: absolute;
		inset: 0;
		border-radius: 10px;
		background: var(--surface);
		border: 1px solid var(--border);
	}
	.stack::before {
		transform: translate(8px, -8px);
		opacity: 0.5;
	}
	.stack::after {
		transform: translate(4px, -4px);
		opacity: 0.8;
	}
	.card {
		position: relative;
		z-index: 1;
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 10px;
		padding: 6px 8px 8px;
		box-shadow: 0 8px 24px rgba(30, 30, 70, 0.1);
	}
	.c4 .card {
		/* header (26) + gap (6) + padding (6) + border (1) above the first row */
		margin-top: calc(var(--pad) - 39px);
	}
	.cardhead {
		height: 26px;
		display: flex;
		align-items: center;
		justify-content: space-between;
		font-size: 12px;
		font-weight: 600;
		margin-bottom: 6px;
	}
	.lt {
		white-space: nowrap;
	}
	.cardhead small {
		color: var(--muted);
		font-weight: 400;
	}
	.nav {
		border: 1px solid var(--border);
		background: var(--surface-2);
		border-radius: 5px;
		width: 22px;
		height: 22px;
		cursor: pointer;
		line-height: 1;
		padding: 0;
	}
	.nav:hover {
		border-color: var(--accent);
	}
	.vitmap {
		line-height: 0;
	}
	.slider {
		width: 100%;
		margin: 8px 0 0;
	}
	.cached {
		display: block;
		font-size: 10px;
		color: var(--muted);
		margin-top: 8px;
		text-align: center;
	}
	.dec .card {
		margin-top: -4px;
	}
	.spark {
		display: flex;
		align-items: flex-end;
		gap: 1px;
		height: 30px;
	}
	.spark button {
		flex: 1;
		height: 100%;
		display: flex;
		align-items: flex-end;
		border: none;
		background: none;
		padding: 0;
		cursor: pointer;
	}
	.spark span {
		width: 100%;
		background: color-mix(in srgb, var(--dec) 45%, transparent);
		border-radius: 1px 1px 0 0;
	}
	.spark button.on span {
		background: var(--dec);
	}
	.share {
		font-size: 10.5px;
		color: var(--muted);
		margin: 4px 0 8px;
	}
	.share b {
		color: var(--dec);
	}
	.outbox {
		background: var(--surface);
		border: 1.5px solid var(--out);
		border-radius: 10px;
		padding: 8px 10px;
		box-shadow: 0 8px 24px rgba(20, 90, 60, 0.12);
		margin-bottom: 60px;
	}
	.obhead {
		font-size: 12px;
		font-weight: 600;
		display: flex;
		justify-content: space-between;
		margin-bottom: 6px;
	}
	.obhead span {
		font-family: var(--mono);
		font-weight: 400;
		color: var(--muted);
		font-size: 10.5px;
	}
	.prow {
		display: grid;
		grid-template-columns: 56px 1fr 38px;
		align-items: center;
		gap: 5px;
		font-size: 11px;
		padding: 1px 3px;
		border-radius: 4px;
	}
	.prow.chosen {
		background: color-mix(in srgb, var(--out) 14%, transparent);
		font-weight: 650;
	}
	.ptok {
		font-family: var(--mono);
		white-space: pre;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.pbar {
		height: 7px;
		background: var(--surface-2);
		border-radius: 3px;
		overflow: hidden;
	}
	.pbar span {
		display: block;
		height: 100%;
		background: var(--out);
		transition: width 0.5s cubic-bezier(0.2, 0.8, 0.2, 1);
	}
	.pval {
		font-family: var(--mono);
		font-size: 10px;
		text-align: right;
		color: var(--muted);
	}
	.obfoot {
		font-size: 10px;
		color: var(--muted);
		margin-top: 6px;
	}
</style>
