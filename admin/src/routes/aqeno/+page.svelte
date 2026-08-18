<script lang="ts">
	import { page } from '$app/state';
	import { createQuery } from '@tanstack/svelte-query';
	import { apiRequest } from '$lib/api/client';
	import { connection } from '$lib/api/connection.svelte';
	import { userMessageForError } from '$lib/api/errors';
	import SettingsForm from '$lib/components/settings/SettingsForm.svelte';
	import SourceList from '$lib/components/device/SourceList.svelte';
	import ControlsPanel from '$lib/components/device/ControlsPanel.svelte';
	import Button from '$lib/ui/Button.svelte';
	import { formatBytes } from '$lib/utils/format';
	import type { components } from '$lib/api/schema';

	type DeviceStatus = components['schemas']['DeviceStatus'];
	type DiagnosticsStatus = components['schemas']['DiagnosticsStatus'];

	const section = $derived(page.url.searchParams.get('section') ?? 'device');

	const deviceQuery = createQuery(() => ({
		queryKey: ['device'],
		queryFn: () => apiRequest<DeviceStatus>('/device')
	}));

	const diagnosticsQuery = createQuery(() => ({
		queryKey: ['diagnostics'],
		queryFn: () => apiRequest<DiagnosticsStatus>('/diagnostics')
	}));

	const tabs = $derived([
		{ id: 'device', label: 'Gerät', href: '/aqeno' },
		...(deviceQuery.data?.capabilities.includes('physical_controls')
			? [{ id: 'controls', label: 'Bedienung', href: '/aqeno?section=controls' }]
			: []),
		{ id: 'storage', label: 'Speicherorte', href: '/aqeno?section=storage' },
		{ id: 'settings', label: 'Einstellungen', href: '/aqeno?section=settings' }
	]);

	const activeTab = $derived(
		section === 'controls'
			? 'controls'
			: section === 'storage'
				? 'storage'
				: section === 'settings'
					? 'settings'
					: 'device'
	);

	const usedPct = $derived(
		deviceQuery.data
			? Math.round(
					((deviceQuery.data.storage_total_bytes - deviceQuery.data.storage_free_bytes) /
						deviceQuery.data.storage_total_bytes) *
						100
				)
			: 0
	);

	let currentPassword = $state('');
	let newPassword = $state('');
	let repeatedPassword = $state('');
	let passwordMessage = $state<string | null>(null);
	let passwordError = $state<string | null>(null);
	let changingPassword = $state(false);

	async function changePassword() {
		passwordMessage = null;
		passwordError = null;
		if (newPassword !== repeatedPassword) {
			passwordError = 'Die neuen Passwörter stimmen nicht überein.';
			return;
		}
		changingPassword = true;
		try {
			const session = await apiRequest<{ csrf_token: string }>('/auth/password', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ current_password: currentPassword, new_password: newPassword })
			});
			connection.connect(
				connection.baseUrl,
				session.csrf_token,
				connection.deviceName ?? 'AQENO'
			);
			currentPassword = '';
			newPassword = '';
			repeatedPassword = '';
			passwordMessage = 'Das Verwaltungspasswort wurde geändert.';
		} catch (error) {
			passwordError = userMessageForError(error);
		} finally {
			changingPassword = false;
		}
	}

	async function logout() {
		try {
			await apiRequest<void>('/auth/logout', { method: 'POST' });
		} finally {
			connection.disconnect();
		}
	}
</script>

<div class="mx-auto max-w-2xl px-4 py-6 lg:px-8 lg:py-10">
	<header class="mb-6">
		<h1 class="text-display">AQENO</h1>
		<p class="mt-2 text-body text-ink-muted">Gerät, Speicher und Einstellungen.</p>
	</header>

	<nav class="mb-8 flex gap-2 overflow-x-auto pb-1" aria-label="AQENO Bereiche">
		{#each tabs as tab (tab.id)}
			<a
				href={tab.href}
				class="shrink-0 rounded-full px-4 py-2 text-caption font-medium transition-colors {activeTab ===
				tab.id
					? 'bg-accent-soft text-accent'
					: 'bg-surface text-ink-muted hover:bg-surface-muted'}"
			>
				{tab.label}
			</a>
		{/each}
	</nav>

	{#if activeTab === 'device'}
		{#if deviceQuery.data}
			<section class="rounded-[var(--radius-xl)] bg-surface p-5 shadow-sm">
				<div class="flex items-start gap-3">
					<span
						class="mt-1.5 inline-block h-2.5 w-2.5 rounded-full {deviceQuery.data.readiness ===
						'ready'
							? 'bg-success'
							: 'bg-attention'}"
					></span>
					<div>
						<p class="text-title">
							{deviceQuery.data.readiness === 'ready'
								? 'AQENO läuft einwandfrei'
								: 'AQENO startet noch'}
						</p>
						<p class="mt-1 text-caption text-ink-muted">
							{deviceQuery.data.name} · Version {deviceQuery.data.aqeno_version}
						</p>
					</div>
				</div>

				<div class="mt-5">
					<div class="flex justify-between text-caption">
						<span>Speicher</span>
						<span class="text-ink-muted"
							>{formatBytes(deviceQuery.data.storage_free_bytes)} frei</span
						>
					</div>
					<div class="mt-2 h-2 overflow-hidden rounded-full bg-surface-muted">
						<div class="h-full bg-accent" style="width: {usedPct}%"></div>
					</div>
				</div>

				{#if diagnosticsQuery.data}
					<details class="mt-5">
						<summary class="cursor-pointer text-caption text-ink-muted">Technische Details</summary>
						<dl class="mt-2 space-y-1 text-caption text-ink-muted">
							<div class="flex justify-between">
								<dt>Audio</dt>
								<dd>{diagnosticsQuery.data.audio}</dd>
							</div>
							<div class="flex justify-between">
								<dt>Display</dt>
								<dd>{diagnosticsQuery.data.display}</dd>
							</div>
							<div class="flex justify-between">
								<dt>NFC</dt>
								<dd>{diagnosticsQuery.data.nfc}</dd>
							</div>
							<div class="flex justify-between">
								<dt>Datenbank</dt>
								<dd>{diagnosticsQuery.data.database}</dd>
							</div>
						</dl>
					</details>
				{/if}
			</section>
		{/if}
	{:else if activeTab === 'controls'}
		<ControlsPanel />
	{:else if activeTab === 'storage'}
		<SourceList />
	{:else}
		<div class="space-y-8">
			<SettingsForm />
			<section class="rounded-[var(--radius-xl)] border border-border bg-surface p-5 shadow-sm">
				<h2 class="text-title">Verwaltung</h2>
				<p class="mt-1 text-caption text-ink-muted">
					Dieses Passwort schützt nur die lokale AQENO-Administration.
				</p>
				<form
					class="mt-5 grid gap-4"
					onsubmit={(event) => {
						event.preventDefault();
						void changePassword();
					}}
				>
					<label class="grid gap-1.5 text-caption font-medium">
						Aktuelles Passwort
						<input class="min-h-12 rounded-[var(--radius-md)] border border-border bg-surface-muted px-3 text-body font-normal" type="password" bind:value={currentPassword} autocomplete="current-password" required />
					</label>
					<label class="grid gap-1.5 text-caption font-medium">
						Neues Passwort
						<input class="min-h-12 rounded-[var(--radius-md)] border border-border bg-surface-muted px-3 text-body font-normal" type="password" bind:value={newPassword} autocomplete="new-password" minlength="10" required />
					</label>
					<label class="grid gap-1.5 text-caption font-medium">
						Neues Passwort wiederholen
						<input class="min-h-12 rounded-[var(--radius-md)] border border-border bg-surface-muted px-3 text-body font-normal" type="password" bind:value={repeatedPassword} autocomplete="new-password" minlength="10" required />
					</label>
					{#if passwordError}<p class="text-caption text-danger" role="alert">{passwordError}</p>{/if}
					{#if passwordMessage}<p class="text-caption text-success" role="status">{passwordMessage}</p>{/if}
					<div class="flex flex-wrap gap-3">
						<Button type="submit" disabled={changingPassword}>
							{changingPassword ? 'Ändern …' : 'Passwort ändern'}
						</Button>
						<Button variant="ghost" onclick={() => void logout()}>Abmelden</Button>
					</div>
				</form>
			</section>
		</div>
	{/if}
</div>
