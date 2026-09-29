import { flow, LAST_STAGE } from '../state.svelte.js';

let raf = 0;
let token = 0;

/** Pulse through stages `from..to`, calling onStage(k) when stage k completes. */
export function runFlow(from, to, { stageMs = 560, onStage } = {}) {
	stopFlow();
	const my = ++token;
	flow.lit = from - 1;
	flow.running = from;
	flow.t = 0;
	return new Promise((resolve) => {
		let stage = from;
		let start = performance.now();
		const tick = (now) => {
			if (my !== token) return resolve(false);
			const t = (now - start) / stageMs;
			if (t >= 1) {
				flow.lit = stage;
				onStage?.(stage);
				stage++;
				if (stage > to) {
					flow.running = -1;
					flow.t = 0;
					return resolve(true);
				}
				flow.running = stage;
				flow.t = 0;
				start = now;
			} else {
				flow.t = easeInOut(t);
			}
			raf = requestAnimationFrame(tick);
		};
		raf = requestAnimationFrame(tick);
	});
}

export function stopFlow() {
	token++;
	cancelAnimationFrame(raf);
	flow.running = -1;
	flow.t = 0;
	flow.lit = LAST_STAGE;
}

const easeInOut = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);

/** Is a node that is reached by stage k visible yet? */
export const reached = (k) => flow.lit >= k || (flow.running === k && flow.t > 0.8);
