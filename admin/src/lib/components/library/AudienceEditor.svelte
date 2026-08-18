<script lang="ts">
	import { createQuery, useQueryClient } from '@tanstack/svelte-query';
	import { apiRequest } from '$lib/api/client';
	import Avatar from '$lib/components/primitives/Avatar.svelte';
	import Button from '$lib/components/primitives/Button.svelte';
	import type { components } from '$lib/api/schema';

	type ProfileResource = components['schemas']['ProfileResource'];
	type EffectiveAccessResource = components['schemas']['EffectiveAccessResource'];

	type Props = {
		mediaId: string;
	};

	let { mediaId }: Props = $props();

	const queryClient = useQueryClient();

	const profilesQuery = createQuery(() => ({
		queryKey: ['profiles'],
		queryFn: () => apiRequest<ProfileResource[]>('/profiles')
	}));

	let mode = $state<'shared' | 'selected'>('shared');
	let selectedProfiles = $state<Set<string>>(new Set());
	let saving = $state(false);
	let loaded = $state(false);

	$effect(() => {
		if (!profilesQuery.data || loaded) return;
		void loadCurrentAccess();
	});

	async function loadCurrentAccess() {
		if (!profilesQuery.data) return;
		const results = await Promise.all(
			profilesQuery.data.map((p) =>
				apiRequest<EffectiveAccessResource>(`/library/media/${mediaId}/access/${p.name}`)
			)
		);
		const allowed = results.filter((r) => r.allowed).map((r) => r.profile_name);
		if (results.every((r) => r.source === 'shared_default' && r.allowed)) {
			mode = 'shared';
		} else {
			mode = 'selected';
			selectedProfiles = new Set(allowed);
		}
		loaded = true;
	}

	function toggleProfile(name: string) {
		const next = new Set(selectedProfiles);
		if (next.has(name)) next.delete(name);
		else next.add(name);
		selectedProfiles = next;
	}

	async function save() {
		saving = true;
		try {
			await apiRequest('/content-access/bulk', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					media_ids: [mediaId],
					operation: mode === 'shared' ? 'set_shared' : 'set_selected_profiles',
					profile_names: mode === 'selected' ? [...selectedProfiles] : undefined
				})
			});
			loaded = false;
			await loadCurrentAccess();
			await queryClient.invalidateQueries({ queryKey: ['library'] });
		} finally {
			saving = false;
		}
	}
</script>

<section class="rounded-card border border-border p-4">
	<h4 class="text-sm font-semibold text-text-primary">Sichtbarkeit</h4>
	<p class="mt-1 text-xs text-text-secondary">Welche Profile diesen Inhalt sehen dürfen.</p>

	<div class="mt-3 space-y-2">
		<label class="flex cursor-pointer items-center gap-2 text-sm">
			<input type="radio" name="audience-{mediaId}" checked={mode === 'shared'} onchange={() => (mode = 'shared')} />
			Alle Profile
		</label>
		<label class="flex cursor-pointer items-center gap-2 text-sm">
			<input
				type="radio"
				name="audience-{mediaId}"
				checked={mode === 'selected'}
				onchange={() => (mode = 'selected')}
			/>
			Ausgewählte Profile
		</label>
	</div>

	{#if mode === 'selected' && profilesQuery.data}
		<div class="mt-3 space-y-2">
			{#each profilesQuery.data as profile (profile.name)}
				<label class="flex cursor-pointer items-center gap-3 rounded-button px-2 py-2 hover:bg-surface-sunken">
					<input
						type="checkbox"
						checked={selectedProfiles.has(profile.name)}
						onchange={() => toggleProfile(profile.name)}
					/>
					<Avatar name={profile.name} size="sm" />
					<span class="text-sm font-medium">{profile.name}</span>
				</label>
			{/each}
		</div>
	{/if}

	<Button class="mt-3" disabled={saving} onclick={() => void save()}>
		{saving ? 'Speichern …' : 'Speichern'}
	</Button>
</section>
