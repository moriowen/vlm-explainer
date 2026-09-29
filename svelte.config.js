import adapter from '@sveltejs/adapter-static';

export default {
	kit: {
		adapter: adapter({ fallback: undefined }),
		paths: { base: process.env.BASE_PATH ?? '' }
	}
};
