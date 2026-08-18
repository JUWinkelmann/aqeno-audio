<script lang="ts">
	import { onMount } from 'svelte';
	import { apiRequest } from '$lib/api/client';
	import { connection } from '$lib/api/connection.svelte';
	import { userMessageForError } from '$lib/api/errors';
	import Button from '$lib/components/primitives/Button.svelte';

	type AuthStatus = {
		setup_required: boolean;
		authenticated: boolean;
		csrf_token: string | null;
	};
	type Session = { csrf_token: string; expires_in_seconds: number };
	type Confirmation = { id: string; state: 'pending' | 'confirmed' };
	type Device = { name: string };
	type Mode = 'loading' | 'login' | 'setup' | 'confirm-setup' | 'confirm-recovery' | 'password';

	let mode = $state<Mode>('loading');
	let baseUrl = $state(connection.baseUrl);
	let password = $state('');
	let passwordRepeat = $state('');
	let confirmationId = $state<string | null>(null);
	let error = $state<string | null>(null);
	let busy = $state(false);
	let recovery = $state(false);

	async function raw<T>(path: string, options: RequestInit = {}): Promise<T> {
		const response = await fetch(`${baseUrl.replace(/\/$/, '')}${path}`, {
			...options,
			credentials: 'include',
			headers: { 'Content-Type': 'application/json', ...options.headers }
		});
		if (!response.ok) {
			const body = (await response.json()) as { error?: { message?: string; code?: string } };
			if (body.error?.code === 'password_incorrect') throw new Error('Das Passwort ist nicht korrekt.');
			if (body.error?.code === 'auth_rate_limited')
				throw new Error('Zu viele Versuche. Bitte versuche es in Kürze erneut.');
			if (body.error?.code === 'physical_confirmation_required')
				throw new Error('Die Bestätigung ist abgelaufen. Bitte starte sie erneut.');
			if (body.error?.code === 'password_policy')
				throw new Error('Das Passwort muss mindestens 10 Zeichen lang sein.');
			if (body.error?.code === 'setup_state_invalid')
				throw new Error('Die Verwaltung konnte nicht eingerichtet werden. Bitte starte erneut.');
			throw new Error(body.error?.message ?? 'AQENO ist gerade nicht erreichbar.');
		}
		return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
	}

	async function completeSession(session: Session) {
		connection.baseUrl = baseUrl.replace(/\/$/, '');
		connection.csrfToken = session.csrf_token;
		const device = await apiRequest<Device>('/device');
		connection.connect(connection.baseUrl, session.csrf_token, device.name);
	}

	async function discover() {
		error = null;
		try {
			const status = await raw<AuthStatus>('/auth/status');
			if (status.authenticated && status.csrf_token) {
				await completeSession({ csrf_token: status.csrf_token, expires_in_seconds: 0 });
				return;
			}
			mode = status.setup_required ? 'setup' : 'login';
		} catch (err) {
			error = err instanceof Error ? err.message : userMessageForError(err);
			mode = 'login';
		}
	}

	async function login() {
		busy = true;
		error = null;
		try {
			await completeSession(
				await raw<Session>('/auth/login', { method: 'POST', body: JSON.stringify({ password }) })
			);
		} catch (err) {
			error = err instanceof Error ? err.message : userMessageForError(err);
		} finally {
			busy = false;
		}
	}

	async function beginConfirmation(purpose: 'setup' | 'recovery') {
		busy = true;
		error = null;
		try {
			const confirmation = await raw<Confirmation>(`/auth/${purpose}/confirmations`, {
				method: 'POST'
			});
			confirmationId = confirmation.id;
			recovery = purpose === 'recovery';
			mode = purpose === 'setup' ? 'confirm-setup' : 'confirm-recovery';
			void pollConfirmation(purpose, confirmation.id);
		} catch (err) {
			error = err instanceof Error ? err.message : userMessageForError(err);
		} finally {
			busy = false;
		}
	}

	async function pollConfirmation(purpose: 'setup' | 'recovery', id: string) {
		while (confirmationId === id && mode.startsWith('confirm')) {
			await new Promise((resolve) => setTimeout(resolve, 1000));
			try {
				const current = await raw<Confirmation>(`/auth/${purpose}/confirmations/${id}`);
				if (current.state === 'confirmed') {
					mode = 'password';
					return;
				}
			} catch (err) {
				error = err instanceof Error ? err.message : userMessageForError(err);
				mode = purpose === 'setup' ? 'setup' : 'login';
				return;
			}
		}
	}

	async function setPassword() {
		if (password !== passwordRepeat) {
			error = 'Die Passwörter stimmen nicht überein.';
			return;
		}
		if (!confirmationId) return;
		busy = true;
		error = null;
		try {
			const path = recovery ? '/auth/recovery' : '/auth/setup';
			const session = await raw<Session>(path, {
				method: 'POST',
				body: JSON.stringify({ confirmation_id: confirmationId, password })
			});
			await completeSession(session);
		} catch (err) {
			error = err instanceof Error ? err.message : userMessageForError(err);
		} finally {
			busy = false;
		}
	}

	onMount(() => void discover());
</script>

<div class="flex min-h-dvh items-center justify-center px-4 py-12">
	<div class="w-full max-w-md rounded-card bg-surface-raised p-8 shadow-(--shadow-float)">
		<div class="mb-8 text-center">
			<p class="text-sm font-medium tracking-wide text-accent uppercase">AQENO</p>
			<h1 class="mt-2 text-2xl font-semibold text-text-primary">
				{mode === 'setup' || mode === 'confirm-setup' || (mode === 'password' && !recovery)
					? 'Verwaltung einrichten'
					: 'Verwaltung'}
			</h1>
		</div>

		{#if mode === 'loading'}
			<p class="text-center text-sm text-text-secondary">AQENO wird gesucht …</p>
		{:else if mode === 'setup'}
			<p class="mb-6 text-sm text-text-secondary">
				Bestätige einmal direkt an deinem AQENO, dass du die Verwaltung einrichten möchtest.
			</p>
			<Button class="w-full" disabled={busy} onclick={() => void beginConfirmation('setup')}>
				Verwaltung einrichten
			</Button>
		{:else if mode === 'confirm-setup' || mode === 'confirm-recovery'}
			<div class="space-y-4 text-center" role="status">
				<div class="mx-auto flex size-16 items-center justify-center rounded-full bg-accent/10 text-2xl text-accent">●</div>
				<p class="font-medium text-text-primary">Drücke am AQENO nacheinander links, Mitte und rechts.</p>
				<p class="text-sm text-text-secondary">Die Bestätigung ist nur für kurze Zeit gültig.</p>
			</div>
		{:else if mode === 'password'}
			<form class="space-y-4" onsubmit={(event) => { event.preventDefault(); void setPassword(); }}>
				<label class="block space-y-1.5">
					<span class="text-sm font-medium text-text-primary">Neues Passwort</span>
					<input class="w-full rounded-button border border-border bg-surface-sunken px-3 py-2.5 outline-none focus:border-accent" type="password" bind:value={password} autocomplete="new-password" minlength="10" required />
				</label>
				<label class="block space-y-1.5">
					<span class="text-sm font-medium text-text-primary">Passwort wiederholen</span>
					<input class="w-full rounded-button border border-border bg-surface-sunken px-3 py-2.5 outline-none focus:border-accent" type="password" bind:value={passwordRepeat} autocomplete="new-password" minlength="10" required />
				</label>
				<p class="text-xs text-text-secondary">Mindestens 10 Zeichen. Eine gut merkbare Passphrase ist ideal.</p>
				<Button type="submit" class="w-full" disabled={busy}>Passwort speichern</Button>
			</form>
		{:else}
			<form class="space-y-4" onsubmit={(event) => { event.preventDefault(); void login(); }}>
				<label class="block space-y-1.5">
					<span class="text-sm font-medium text-text-primary">Passwort</span>
					<input class="w-full rounded-button border border-border bg-surface-sunken px-3 py-2.5 outline-none focus:border-accent" type="password" bind:value={password} autocomplete="current-password" required />
				</label>
				<Button type="submit" class="w-full" disabled={busy}>{busy ? 'Anmeldung …' : 'Anmelden'}</Button>
				<button type="button" class="w-full text-sm text-text-secondary underline-offset-4 hover:underline" onclick={() => void beginConfirmation('recovery')}>Passwort vergessen?</button>
				<details class="pt-3 text-sm text-text-secondary">
					<summary class="cursor-pointer">Verbindungsdiagnose</summary>
					<label class="mt-3 block space-y-1.5">
						<span>API-Adresse</span>
						<input class="w-full rounded-button border border-border bg-surface-sunken px-3 py-2" type="url" bind:value={baseUrl} autocomplete="url" />
					</label>
				</details>
			</form>
		{/if}

		{#if error}<p class="mt-4 rounded-button bg-danger/10 px-3 py-2 text-sm text-danger" role="alert">{error}</p>{/if}
	</div>
</div>
