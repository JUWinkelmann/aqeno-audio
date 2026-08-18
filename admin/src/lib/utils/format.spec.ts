import { formatDuration, formatBytes } from '$lib/utils/format';
import { describe, expect, it } from 'vitest';

describe('formatDuration', () => {
	it('formats minutes', () => {
		expect(formatDuration(120)).toBe('2 Min');
	});

	it('formats hours', () => {
		expect(formatDuration(3660)).toBe('1 Std 1 Min');
	});
});

describe('formatBytes', () => {
	it('formats gigabytes', () => {
		expect(formatBytes(2 * 1024 ** 3)).toBe('2.0 GB');
	});
});
