import { buildLibraryPath, filterToQueryParams } from '$lib/api/library';
import { describe, expect, it } from 'vitest';

describe('buildLibraryPath', () => {
	it('includes search and kind parameters', () => {
		const path = buildLibraryPath({ search: 'Pettersson', kind: 'audio_drama', limit: 50 });
		expect(path).toContain('search=Pettersson');
		expect(path).toContain('kind=audio_drama');
	});
});

describe('filterToQueryParams', () => {
	it('maps unavailable filter', () => {
		const params = filterToQueryParams({ type: 'unavailable' }, '', null);
		expect(params.available).toBe(false);
	});
});
