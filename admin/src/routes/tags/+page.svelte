<script lang="ts">
	import { createQuery } from '@tanstack/svelte-query';
	import { apiRequest, artworkUrl } from '$lib/api/client';
	import Artwork from '$lib/ui/Artwork.svelte';
	import Button from '$lib/ui/Button.svelte';
	import TokenAssignWizard from '$lib/components/tokens/TokenAssignWizard.svelte';
	import type { components } from '$lib/api/schema';
	import { ArrowRight, Nfc } from '@lucide/svelte';

	type TokenResource = components['schemas']['TokenResource'];
	type MediaDetail = components['schemas']['MediaDetail'];

	let assignOpen = $state(false);

	const tokensQuery = createQuery(() => ({
		queryKey: ['tokens'],
		queryFn: () => apiRequest<TokenResource[]>('/tokens')
	}));

	let mediaById = $state<Record<string, MediaDetail>>({});

	$effect(() => {
		if (!tokensQuery.data) return;
		for (const token of tokensQuery.data) {
			const mediaId = token.assigned_media_id;
			if (mediaId && !mediaById[mediaId]) {
				void apiRequest<MediaDetail>(`/library/media/${mediaId}`).then((media) => {
					mediaById = { ...mediaById, [mediaId]: media };
				});
			}
		}
	});
</script>

<div class="mx-auto max-w-2xl px-4 py-6 lg:px-8 lg:py-10">
	<header class="mb-8 flex items-start justify-between gap-4">
		<div>
			<h1 class="text-display">Tags</h1>
			<p class="mt-2 text-body text-ink-muted">
				Halte eine Karte oder Figur an AQENO — dann ordne sie einem Inhalt zu.
			</p>
		</div>
		<Button onclick={() => (assignOpen = true)}>Tag zuordnen</Button>
	</header>

	{#if tokensQuery.isPending}
		<div class="space-y-3">
			{#each Array(3) as _, i (i)}
				<div class="h-24 animate-pulse rounded-[var(--radius-lg)] bg-surface-muted"></div>
			{/each}
		</div>
	{:else if !tokensQuery.data?.length}
		<div class="rounded-[var(--radius-xl)] border border-dashed border-border bg-surface p-8 text-center">
			<Nfc size={32} class="mx-auto text-ink-faint" />
			<p class="mt-4 text-title">Noch kein Tag zugeordnet</p>
			<p class="mt-2 text-body text-ink-muted">
				Halte eine Karte an AQENO und tippe auf „Tag zuordnen".
			</p>
			<Button class="mt-6" onclick={() => (assignOpen = true)}>Tag zuordnen</Button>
		</div>
	{:else}
		<div class="space-y-3">
			{#each tokensQuery.data as token (token.uid)}
				{@const media = token.assigned_media_id ? mediaById[token.assigned_media_id] : null}
				<article class="flex items-center gap-4 rounded-[var(--radius-lg)] bg-surface p-4 shadow-sm">
					<div
						class="flex h-14 w-14 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-surface-muted"
					>
						<Nfc size={22} class="text-accent" />
					</div>
					<ArrowRight size={16} class="shrink-0 text-ink-faint" />
					<div class="h-14 w-14 shrink-0 overflow-hidden rounded-[var(--radius-md)]">
						{#if media}
							<Artwork
								title={media.title}
								kind={media.kind}
								src={artworkUrl(media.artwork_thumbnail_url)}
								hue={(media.title.charCodeAt(0) * 17) % 360}
								size="sm"
							/>
						{:else}
							<div
								class="flex h-full w-full items-center justify-center bg-surface-muted text-ink-faint"
							>
								?
							</div>
						{/if}
					</div>
					<div class="min-w-0 flex-1">
						<p class="truncate text-body font-medium">{media?.title ?? 'Nicht zugeordnet'}</p>
						<p class="truncate text-caption text-ink-faint" title={token.uid}>
							{token.uid.slice(0, 12)}…
						</p>
					</div>
				</article>
			{/each}
		</div>
	{/if}
</div>

<TokenAssignWizard open={assignOpen} onclose={() => (assignOpen = false)} />
