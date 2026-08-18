<script lang="ts">
	import { createQuery } from '@tanstack/svelte-query';
	import { apiRequest } from '$lib/api/client';
	import { importStore } from '$lib/stores/import.svelte';
	import type { components } from '$lib/api/schema';
	import { formatBytes } from '$lib/utils/format';
	import { artworkUrl } from '$lib/api/client';
	import Artwork from '$lib/ui/Artwork.svelte';
	import { Plus } from '@lucide/svelte';

	type DeviceStatus = components['schemas']['DeviceStatus'];
	type PlaybackStatus = components['schemas']['PlaybackStatus'];
	type OperationResponse = components['schemas']['OperationResponse'];
	type MediaPage = components['schemas']['MediaPage'];

	const deviceQuery = createQuery(() => ({
		queryKey: ['device'],
		queryFn: () => apiRequest<DeviceStatus>('/device')
	}));

	const playbackQuery = createQuery(() => ({
		queryKey: ['playback'],
		queryFn: () => apiRequest<PlaybackStatus>('/playback'),
		refetchInterval: 15_000
	}));

	const opsQuery = createQuery(() => ({
		queryKey: ['operations'],
		queryFn: () => apiRequest<OperationResponse[]>('/operations'),
		refetchInterval: 5000
	}));

	const recentQuery = createQuery(() => ({
		queryKey: ['library', 'recent'],
		queryFn: () => apiRequest<MediaPage>('/library/media?limit=4')
	}));

	const activeOps = $derived(
		opsQuery.data?.filter((o) => o.state === 'queued' || o.state === 'running') ?? []
	);
</script>

<div class="mx-auto max-w-3xl px-4 py-8 lg:px-8 lg:py-12">
	<header class="mb-10">
		{#if deviceQuery.data}
			<p class="text-label uppercase text-ink-muted">Guten Tag</p>
			<h1 class="mt-1 text-display">{deviceQuery.data.name}</h1>
			<p class="mt-2 text-body text-ink-muted">
				{#if deviceQuery.data.readiness === 'ready'}
					AQENO ist bereit.
				{:else}
					AQENO startet noch …
				{/if}
			</p>
		{/if}
	</header>

	<div class="space-y-4">
		<!-- Primary CTA -->
		<button
			type="button"
			class="flex w-full items-center gap-4 rounded-[var(--radius-xl)] bg-accent p-5 text-left text-white shadow-md-token transition-opacity hover:opacity-95"
			onclick={() => importStore.show()}
		>
			<span class="flex h-12 w-12 items-center justify-center rounded-full bg-white/20">
				<Plus size={24} />
			</span>
			<span>
				<span class="block text-title">Inhalte hinzufügen</span>
				<span class="text-caption opacity-80">Musik, Hörspiele, Hörbücher</span>
			</span>
		</button>

		{#if activeOps.length > 0}
			<section class="rounded-[var(--radius-xl)] bg-surface p-5 shadow-sm">
				<p class="text-label uppercase text-ink-muted">Gerade aktiv</p>
				{#each activeOps as op (op.id)}
					<div class="mt-3">
						<p class="text-body font-medium">Bibliothek wird aktualisiert</p>
						<div class="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-muted">
							<div class="h-full bg-accent transition-all" style="width: {op.progress}%"></div>
						</div>
					</div>
				{/each}
			</section>
		{/if}

		{#if playbackQuery.data?.media_id}
			<section class="rounded-[var(--radius-xl)] bg-surface p-5 shadow-sm">
				<p class="text-label uppercase text-ink-muted">Gerade läuft</p>
				<p class="mt-2 text-title">{playbackQuery.data.title}</p>
				{#if playbackQuery.data.chapter_title}
					<p class="text-caption text-ink-muted">{playbackQuery.data.chapter_title}</p>
				{/if}
			</section>
		{/if}

		{#if recentQuery.data?.items.length}
			<section>
				<div class="mb-3 flex items-center justify-between">
					<h2 class="text-title">Mediathek</h2>
					<a href="/library" class="text-caption text-accent">Alle anzeigen</a>
				</div>
				<div class="grid grid-cols-2 gap-3 sm:grid-cols-4">
					{#each recentQuery.data.items as item (item.id)}
						<a href="/library?id={item.id}" class="block">
							<div class="aspect-square overflow-hidden rounded-[var(--radius-md)]">
								<Artwork
									title={item.title}
									kind={item.kind}
									src={artworkUrl(item.artwork_thumbnail_url)}
									hue={(item.title.charCodeAt(0) * 17) % 360}
									size="md"
								/>
							</div>
							<p class="mt-2 line-clamp-2 text-caption font-medium">{item.title}</p>
						</a>
					{/each}
				</div>
			</section>
		{:else if recentQuery.data}
			<section class="rounded-[var(--radius-xl)] border border-dashed border-border bg-surface p-8 text-center">
				<p class="text-title">Deine Mediathek ist noch leer</p>
				<p class="mt-2 text-body text-ink-muted">
					Zieh Hörspiele oder Musik hierher — AQENO erledigt den Rest.
				</p>
			</section>
		{/if}

		{#if deviceQuery.data}
			<p class="text-center text-caption text-ink-faint">
				{formatBytes(deviceQuery.data.storage_free_bytes)} frei
			</p>
		{/if}
	</div>
</div>
