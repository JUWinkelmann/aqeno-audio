import { userMessageForError, ApiError } from '$lib/api/errors';
import { describe, expect, it } from 'vitest';

describe('userMessageForError', () => {
	it('maps known API error codes to German messages', () => {
		const error = new ApiError({
			code: 'authentication_required',
			message: 'Authentication is required.',
			details: null
		});
		expect(userMessageForError(error)).toBe('Bitte melde dich erneut an.');
	});

	it('maps network failures', () => {
		const error = new ApiError({
			code: 'network_error',
			message: 'network',
			details: null
		});
		expect(userMessageForError(error)).toContain('Verbindung');
	});
});
