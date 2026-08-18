<script lang="ts">
	import { createQuery, useQueryClient } from '@tanstack/svelte-query';
	import { apiRequest } from '$lib/api/client';
	import Button from '$lib/components/primitives/Button.svelte';
	import type { components } from '$lib/api/schema';

	type SettingsResource = components['schemas']['SettingsResource'];

	const queryClient = useQueryClient();

	const settingsQuery = createQuery(() => ({
		queryKey: ['settings'],
		queryFn: () => apiRequest<SettingsResource>('/settings')
	}));

	let draft = $state<SettingsResource | null>(null);
	let saved = $state(false);
	let saving = $state(false);

	$effect(() => {
		if (settingsQuery.data && !draft) {
			draft = structuredClone(settingsQuery.data);
		}
	});

	async function save() {
		if (!draft) return;
		saving = true;
		saved = false;
		try {
			await apiRequest('/settings', {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(draft)
			});
			saved = true;
			await queryClient.invalidateQueries({ queryKey: ['settings'] });
		} finally {
			saving = false;
		}
	}
</script>

{#if settingsQuery.isPending || !draft}
	<div class="h-48 animate-pulse rounded-card bg-surface-sunken"></div>
{:else}
	<form
		class="space-y-6"
		onsubmit={(e) => {
			e.preventDefault();
			void save();
		}}
	>
		{#if saved}
			<p class="rounded-card bg-warning/10 px-3 py-2 text-sm text-warning">
				Änderung gespeichert — Neustart von AQENO erforderlich.
			</p>
		{/if}

		<section class="rounded-card border border-border p-4">
			<h3 class="font-semibold">Sprache</h3>
			<select class="mt-2 w-full rounded-button border border-border px-3 py-2" bind:value={draft.language}>
				<option value="de">Deutsch</option>
				<option value="en">English</option>
			</select>
		</section>

		<section class="rounded-card border border-border p-4">
			<h3 class="font-semibold">Mediathek</h3>
			<label class="mt-3 flex items-center gap-2 text-sm">
				<input type="checkbox" bind:checked={draft.library.scan_on_startup} />
				Beim Start scannen
			</label>
			<label class="mt-2 flex items-center gap-2 text-sm">
				<input type="checkbox" bind:checked={draft.library.follow_symlinks} />
				Symbolische Links folgen
			</label>
			<div class="mt-3">
				<p class="text-sm font-medium">Speicherorte</p>
				{#each draft.library.roots as root, i}
					<input
						class="mt-1 w-full rounded-button border border-border px-3 py-2 text-sm font-mono"
						bind:value={draft.library.roots[i]}
					/>
				{/each}
			</div>
		</section>

		<section class="rounded-card border border-border p-4">
			<h3 class="font-semibold">NFC</h3>
			<label class="mt-3 block text-sm">
				Entprellung (ms)
				<input
					type="number"
					class="mt-1 w-full rounded-button border border-border px-3 py-2"
					bind:value={draft.nfc.debounce_ms}
				/>
			</label>
			<label class="mt-2 flex items-center gap-2 text-sm">
				<input type="checkbox" bind:checked={draft.nfc.ack_tone_unassigned} />
				Ton bei nicht zugeordnetem Token
			</label>
		</section>

		<section class="rounded-card border border-border p-4">
			<h3 class="font-semibold">Wiedergabe</h3>
			<label class="mt-3 block text-sm">
				Zurückspulen beim Fortsetzen (Sekunden)
				<input
					type="number"
					class="mt-1 w-full rounded-button border border-border px-3 py-2"
					bind:value={draft.resume.rewind_seconds}
				/>
			</label>
		</section>

		<Button type="submit" disabled={saving}>{saving ? 'Speichern …' : 'Einstellungen speichern'}</Button>
	</form>
{/if}
