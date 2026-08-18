<script lang="ts">
	import { page } from '$app/state';
	import { createQuery, useQueryClient } from '@tanstack/svelte-query';
	import { apiRequest } from '$lib/api/client';
	import Avatar from '$lib/components/primitives/Avatar.svelte';
	import Button from '$lib/ui/Button.svelte';
	import type { components } from '$lib/api/schema';

	type ProfileResource = components['schemas']['ProfileResource'];
	type MediaPage = components['schemas']['MediaPage'];

	const profileName = $derived(page.params.name ?? '');
	const queryClient = useQueryClient();

	const profileQuery = createQuery(() => ({
		queryKey: ['profile', profileName],
		queryFn: () => apiRequest<ProfileResource>(`/profiles/${profileName}`),
		enabled: Boolean(profileName)
	}));

	const mediaQuery = createQuery(() => ({
		queryKey: ['library', 'profile', profileName],
		queryFn: () =>
			apiRequest<MediaPage>(`/library/media?profile_name=${encodeURIComponent(profileName)}&limit=50`),
		enabled: Boolean(profileName)
	}));

	let saving = $state(false);

	async function saveProfile() {
		if (!profileQuery.data) return;
		saving = true;
		try {
			await apiRequest(`/profiles/${profileName}`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(profileQuery.data)
			});
			await queryClient.invalidateQueries({ queryKey: ['profile', profileName] });
		} finally {
			saving = false;
		}
	}
</script>

<div class="mx-auto max-w-2xl px-4 py-6 lg:px-8 lg:py-10">
	<a href="/people" class="text-caption text-accent">← Personen</a>

	{#if profileQuery.data}
		<div class="mt-4 flex items-center gap-4">
			<Avatar name={profileQuery.data.name} />
			<div>
				<h1 class="text-display">{profileQuery.data.name}</h1>
				<p class="text-caption text-ink-muted capitalize">{profileQuery.data.level}</p>
			</div>
		</div>

		<section class="mt-8 rounded-[var(--radius-xl)] bg-surface p-5 shadow-sm">
			<h2 class="text-title">Lautstärke</h2>
			<label class="mt-3 block text-body">
				Maximum
				<input
					type="number"
					class="mt-1 w-full rounded-[var(--radius-md)] border border-border bg-canvas px-3 py-2"
					bind:value={profileQuery.data.volume.maximum}
				/>
			</label>
			<Button class="mt-4" disabled={saving} onclick={() => void saveProfile()}>
				{saving ? 'Speichern …' : 'Speichern'}
			</Button>
			<p class="mt-2 text-caption text-ink-muted">Neustart erforderlich nach Änderung.</p>
		</section>

		<section class="mt-6">
			<h2 class="text-title">Sichtbare Inhalte</h2>
			{#if mediaQuery.data?.items.length}
				<ul class="mt-3 space-y-1">
					{#each mediaQuery.data.items as item (item.id)}
						<li>
							<a
								href="/library?id={item.id}"
								class="block rounded-[var(--radius-md)] px-2 py-2 text-body hover:bg-surface-muted"
							>
								{item.title}
							</a>
						</li>
					{/each}
				</ul>
			{:else}
				<p class="mt-2 text-body text-ink-muted">Keine Inhalte für diese Person.</p>
			{/if}
		</section>
	{/if}
</div>
