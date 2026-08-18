<script lang="ts">
	import { goto } from '$app/navigation';
	import { createQuery } from '@tanstack/svelte-query';
	import { apiRequest } from '$lib/api/client';
	import Avatar from '$lib/components/primitives/Avatar.svelte';
	import type { components } from '$lib/api/schema';
	import { ChevronRight, Nfc, Radio } from '@lucide/svelte';

	type ProfileResource = components['schemas']['ProfileResource'];

	const profilesQuery = createQuery(() => ({
		queryKey: ['profiles'],
		queryFn: () => apiRequest<ProfileResource[]>('/profiles')
	}));
</script>

<div class="mx-auto max-w-2xl px-4 py-6 lg:px-8 lg:py-10">
	<header class="mb-8">
		<h1 class="text-display">Personen</h1>
		<p class="mt-2 text-body text-ink-muted">
			Wer AQENO nutzt — und welche Inhalte für wen sichtbar sind.
		</p>
	</header>

	{#if profilesQuery.isPending}
		<div class="space-y-3">
			{#each Array(2) as _, i (i)}
				<div class="h-20 animate-pulse rounded-[var(--radius-lg)] bg-surface-muted"></div>
			{/each}
		</div>
	{:else if profilesQuery.data?.length}
		<div class="space-y-2">
			{#each profilesQuery.data as profile (profile.name)}
				<button
					type="button"
					class="flex w-full items-center gap-4 rounded-[var(--radius-lg)] bg-surface p-4 text-left shadow-sm transition-shadow hover:shadow-md-token"
					onclick={() => goto(`/people/${profile.name}`)}
				>
					<Avatar name={profile.name} />
					<div class="min-w-0 flex-1">
						<p class="text-body font-medium">{profile.name}</p>
						<p class="text-caption text-ink-muted capitalize">
							{profile.level.replace('_', ' ')}
						</p>
					</div>
					<ChevronRight size={18} class="text-ink-faint" />
				</button>
			{/each}
		</div>
	{:else}
		<div class="rounded-[var(--radius-xl)] border border-dashed border-border bg-surface p-8 text-center">
			<p class="text-title">Noch keine Personen</p>
			<p class="mt-2 text-body text-ink-muted">
				Profile werden auf dem AQENO-Gerät eingerichtet.
			</p>
		</div>
	{/if}

	<nav class="mt-10 space-y-2 lg:hidden">
		<a
			href="/tags"
			class="flex items-center gap-3 rounded-[var(--radius-lg)] bg-surface p-4 shadow-sm"
		>
			<Nfc size={20} class="text-accent" />
			<span class="flex-1 text-body font-medium">Tags</span>
			<ChevronRight size={18} class="text-ink-faint" />
		</a>
		<a
			href="/aqeno"
			class="flex items-center gap-3 rounded-[var(--radius-lg)] bg-surface p-4 shadow-sm"
		>
			<Radio size={20} class="text-accent" />
			<span class="flex-1 text-body font-medium">AQENO</span>
			<ChevronRight size={18} class="text-ink-faint" />
		</a>
	</nav>
</div>
