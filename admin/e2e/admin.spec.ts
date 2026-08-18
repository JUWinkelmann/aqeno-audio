import { expect, test } from '@playwright/test';

test('connect screen when not authenticated', async ({ page }) => {
	await page.route('**/api/v1/auth/status', async (route) => {
		return route.fulfill({
			json: { setup_required: false, authenticated: false, csrf_token: null }
		});
	});
	await page.goto('/');
	await expect(page.getByRole('heading', { name: 'Verwaltung' })).toBeVisible();
	await expect(page.getByLabel('Passwort')).toBeVisible();
});

test('library loads with mocked API', async ({ page }) => {
	await page.addInitScript(() => {
		sessionStorage.setItem(
			'aqeno-admin-connection',
			JSON.stringify({
				baseUrl: 'http://127.0.0.1:8766/api/v1',
				csrfToken: 'test-csrf',
				deviceName: 'Test-AQENO'
			})
		);
	});

	await page.route('**/api/v1/**', async (route) => {
		const url = route.request().url();
		if (url.endsWith('/auth/status')) {
			return route.fulfill({
				json: { setup_required: false, authenticated: true, csrf_token: 'test-csrf' }
			});
		}
		if (url.endsWith('/device')) {
			return route.fulfill({
				json: {
					device_id: '00000000-0000-0000-0000-000000000001',
					name: 'Test-AQENO',
					aqeno_version: '0.1.0',
					readiness: 'ready',
					database_health: 'ok',
					capabilities: [],
					storage_total_bytes: 1000000000,
					storage_free_bytes: 500000000
				}
			});
		}
		if (url.includes('/library/media')) {
			return route.fulfill({
				json: { items: [], next_cursor: null, total: 0 }
			});
		}
		if (url.endsWith('/playback')) {
			return route.fulfill({
				json: {
					state: 'stopped',
					media_id: null,
					title: null,
					chapter_title: null,
					position_seconds: null,
					duration_seconds: null,
					volume: null,
					failure_code: null
				}
			});
		}
		if (url.endsWith('/operations')) {
			return route.fulfill({ json: [] });
		}
		if (url.endsWith('/tokens')) {
			return route.fulfill({ json: [] });
		}
		if (url.endsWith('/media-sources')) {
			return route.fulfill({ json: [] });
		}
		if (url.endsWith('/profiles')) {
			return route.fulfill({ json: [] });
		}
		if (url.endsWith('/events')) {
			return route.fulfill({ status: 200, body: '' });
		}
		return route.fulfill({ status: 404, json: { error: { code: 'not_found', message: 'mock' } } });
	});

	await page.goto('/library');
	await expect(page.getByRole('heading', { name: 'Mediathek' })).toBeVisible();
	await expect(page.getByText('Deine Mediathek ist noch leer')).toBeVisible();
});

test('mobile navigation tabs', async ({ page }) => {
	await page.setViewportSize({ width: 390, height: 844 });
	await page.addInitScript(() => {
		sessionStorage.setItem(
			'aqeno-admin-connection',
			JSON.stringify({
				baseUrl: 'http://127.0.0.1:8766/api/v1',
				csrfToken: 'test-csrf',
				deviceName: 'Test-AQENO'
			})
		);
	});

	await page.route('**/api/v1/**', async (route) => {
		const url = route.request().url();
		if (url.endsWith('/device') || url.endsWith('/playback') || url.endsWith('/operations') || url.endsWith('/tokens') || url.endsWith('/media-sources')) {
			return route.fulfill({ json: url.endsWith('/playback') ? { state: 'stopped', media_id: null, title: null, chapter_title: null, position_seconds: null, duration_seconds: null, volume: null, failure_code: null } : url.endsWith('/operations') || url.endsWith('/tokens') || url.endsWith('/media-sources') ? [] : { device_id: '1', name: 'Test', aqeno_version: '0.1.0', readiness: 'ready', database_health: 'ok', capabilities: [], storage_total_bytes: 1, storage_free_bytes: 1 } });
		}
		if (url.includes('/library/media')) {
			return route.fulfill({ json: { items: [], next_cursor: null, total: 0 } });
		}
		return route.fulfill({ status: 200, body: '' });
	});

	await page.goto('/');
	await expect(page.getByRole('navigation', { name: 'Mobile Navigation' })).toBeVisible();
	await page.getByRole('link', { name: 'Mehr' }).click();
	await expect(page).toHaveURL(/\/people/);
});

test('logout ends the browser session and returns to password login', async ({ page }) => {
	await page.addInitScript(() => {
		sessionStorage.setItem(
			'aqeno-admin-connection',
			JSON.stringify({
				baseUrl: `${window.location.origin}/api/v1`,
				csrfToken: 'test-csrf',
				deviceName: 'Test-AQENO'
			})
		);
	});

	await page.route('**/api/v1/**', async (route) => {
		const url = route.request().url();
		if (url.endsWith('/auth/logout')) {
			expect(route.request().headers()['x-aqeno-csrf']).toBe('test-csrf');
			return route.fulfill({ status: 204 });
		}
		if (url.endsWith('/auth/status')) {
			return route.fulfill({
				json: { setup_required: false, authenticated: false, csrf_token: null }
			});
		}
		if (url.endsWith('/device')) {
			return route.fulfill({
				json: {
					device_id: '00000000-0000-0000-0000-000000000001',
					name: 'Test-AQENO',
					aqeno_version: '0.1.0',
					readiness: 'ready',
					database_health: 'ok',
					capabilities: [],
					storage_total_bytes: 1,
					storage_free_bytes: 1
				}
			});
		}
		if (url.endsWith('/playback')) {
			return route.fulfill({
				json: {
					state: 'stopped', media_id: null, title: null, chapter_title: null,
					position_seconds: null, duration_seconds: null, volume: null, failure_code: null
				}
			});
		}
		if (url.endsWith('/operations')) return route.fulfill({ json: [] });
		if (url.includes('/library/media')) {
			return route.fulfill({ json: { items: [], next_cursor: null, total: 0 } });
		}
		return route.fulfill({ status: 404 });
	});

	await page.goto('/');
	await page.getByRole('button', { name: 'Abmelden' }).click();
	await expect(page.getByRole('heading', { name: 'Verwaltung' })).toBeVisible();
	await expect(page.getByLabel('Passwort')).toBeVisible();
});

test('active settings view changes the local administration password', async ({ page }) => {
	await page.addInitScript(() => {
		sessionStorage.setItem(
			'aqeno-admin-connection',
			JSON.stringify({
				baseUrl: `${window.location.origin}/api/v1`,
				csrfToken: 'old-csrf',
				deviceName: 'Test-AQENO'
			})
		);
	});

	await page.route('**/api/v1/**', async (route) => {
		const url = route.request().url();
		if (url.endsWith('/auth/password')) {
			expect(route.request().headers()['x-aqeno-csrf']).toBe('old-csrf');
			expect(route.request().postDataJSON()).toEqual({
				current_password: 'altes passwort',
				new_password: 'neues passwort'
			});
			return route.fulfill({ json: { csrf_token: 'new-csrf', expires_in_seconds: 43_200 } });
		}
		if (url.endsWith('/settings')) {
			return route.fulfill({
				json: {
					language: 'de',
					library: { roots: ['/media'], scan_on_startup: true, follow_symlinks: false },
					nfc: { debounce_ms: 500, ack_tone_unassigned: true },
					resume: { rewind_seconds: 5 }
				}
			});
		}
		if (url.endsWith('/device')) {
			return route.fulfill({
				json: {
					device_id: '00000000-0000-0000-0000-000000000001', name: 'Test-AQENO',
					aqeno_version: '0.1.0', readiness: 'ready', database_health: 'ok', capabilities: [],
					storage_total_bytes: 100, storage_free_bytes: 50
				}
			});
		}
		if (url.endsWith('/diagnostics')) {
			return route.fulfill({
				json: { functional: true, readiness: 'ready', database: 'ok', storage_writable: true,
					audio: 'ready', display: 'ready', nfc: 'ready', physical_controls: 'ready',
					last_playback_error: null }
			});
		}
		return route.fulfill({ status: 404 });
	});

	await page.goto('/aqeno?section=settings');
	await page.getByLabel('Aktuelles Passwort').fill('altes passwort');
	await page.getByLabel('Neues Passwort', { exact: true }).fill('neues passwort');
	await page.getByLabel('Neues Passwort wiederholen').fill('neues passwort');
	await page.getByRole('button', { name: 'Passwort ändern' }).click();
	await expect(page.getByText('Das Verwaltungspasswort wurde geändert.')).toBeVisible();
});
