import { describe, expect, it, vi, beforeEach } from 'vitest';
import { connection } from '$lib/api/connection.svelte';

describe('connection', () => {
	beforeEach(() => {
		connection.disconnect();
	});

	it('connects and persists session state', () => {
		connection.connect('http://127.0.0.1:8766/api/v1', 'csrf-token', 'Wohnzimmer');
		expect(connection.isConnected).toBe(true);
		expect(connection.deviceName).toBe('Wohnzimmer');
	});

	it('disconnects', () => {
		connection.connect('http://127.0.0.1:8766/api/v1', 'csrf-token', 'Wohnzimmer');
		connection.disconnect();
		expect(connection.isConnected).toBe(false);
	});
});
