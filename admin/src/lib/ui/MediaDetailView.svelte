<script lang="ts">
	import { createQuery, useQueryClient } from '@tanstack/svelte-query';
	import { apiRequest, artworkUrl } from '$lib/api/client';
	import Artwork from '$lib/ui/Artwork.svelte';
	import ArtworkSheet from '$lib/ui/ArtworkSheet.svelte';
	import Button from '$lib/ui/Button.svelte';
	import AudienceEditor from '$lib/components/library/AudienceEditor.svelte';
	import type { components } from '$lib/api/schema';
	import { formatDuration } from '$lib/utils/format';
	import { kindLabel } from '$lib/utils/kinds';
	import { Nfc, Trash2, X } from '@lucide/svelte';

	type MediaDetail = components['schemas']['MediaDetail'];

	type Props = {
		mediaId: string;
		onclose?: () => void;
		ontag?: () => void;
	};

	let { mediaId, onclose, ontag }: Props = $props();

	const queryClient = useQueryClient();

	const detailQuery = createQuery(() => ({
		queryKey: ['media', mediaId],
		queryFn: () => apiRequest<MediaDetail>(`/library/media/${mediaId}`)
	}));

	let artworkOpen = $state(false);
	let editingTitle = $state(false);
	let titleDraft = $state('');
	let showDelete = $state(false);

	$effect(() => {
		if (detailQuery.data) titleDraft = detailQuery.data.title;
	});

	async function saveTitle() {
		await apiRequest(`/library/media/${mediaId}`, {
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ title: titleDraft })
		});
		editingTitle = false;
		await queryClient.invalidateQueries({ queryKey: ['media', mediaId] });
		await queryClient.invalidateQueries({ queryKey: ['library'] });
	}

	async function remove() {
		await apiRequest(`/library/media/${mediaId}`, { method: 'DELETE' });
		await queryClient.invalidateQueries({ queryKey: ['library'] });
		onclose?.();
	}
</script>

{#if detailQuery.isPending}
	<div class="animate-pulse space-y-4 p-6">
		<div class="mx-auto aspect-square max-w-xs rounded-[var(--radius-xl)] bg-surface-muted"></div>
	</div>
{:else if detailQuery.data}
	{@const media = detailQuery.data}
	{@const art = artworkUrl(media.artwork_url ?? media.artwork_thumbnail_url)}
	{@const hue = (media.title.charCodeAt(0) * 17) % 360}

	<div class="flex h-full flex-col bg-surface lg:rounded-[var(--radius-xl)] lg:border lg:border-border">
		<div class="flex items-center justify-between border-b border-border px-4 py-3 lg:hidden">
			<button type="button" class="p-2" onclick={() => onclose?.()} aria-label="Zurück">
				<X size={22} />
			</button>
			<span class="text-caption text-ink-muted">Details</span>
			<div class="w-10"></div>
		</div>

		<div class="flex-1 overflow-y-auto">
			<div class="p-6">
				<div class="mx-auto aspect-square max-w-[280px] shadow-artwork">
					<Artwork
						title={media.title}
						kind={media.kind}
						src={art}
						{hue}
						size="hero"
						editable
						onedit={() => (artworkOpen = true)}
					/>
				</div>

				<div class="mt-6 text-center lg:text-left">
					{#if editingTitle}
						<form
							class="flex gap-2"
							onsubmit={(e) => {
								e.preventDefault();
								void saveTitle();
							}}
						>
							<input
								class="flex-1 rounded-[var(--radius-md)] border border-border bg-canvas px-3 py-2 text-body"
								bind:value={titleDraft}
							/>
							<Button type="submit">OK</Button>
						</form>
					{:else}
						<button
							type="button"
							class="text-display text-left"
							onclick={() => (editingTitle = true)}
						>
							{media.title}
						</button>
					{/if}
					<p class="mt-2 text-body text-ink-muted">
						{kindLabel(media.kind)}
						{#if media.chapters.length > 0}
							· {media.chapters.length} Kapitel
						{/if}
						{#if media.duration_seconds}
							· {formatDuration(media.duration_seconds)}
						{/if}
					</p>
					{#if !media.available}
						<p class="mt-2 text-caption text-attention">Momentan nicht erreichbar</p>
					{/if}
				</div>

				<div class="mt-6 flex flex-wrap justify-center gap-2 lg:justify-start">
					<Button variant="soft" onclick={() => ontag?.()}>
						<Nfc size={16} />
						Tag zuordnen
					</Button>
					<Button variant="ghost" onclick={() => (showDelete = true)}>
						<Trash2 size={16} />
						Entfernen
					</Button>
				</div>
			</div>

			{#if media.chapters.length > 0}
				<section class="border-t border-border px-6 py-5">
					<h3 class="text-label uppercase text-ink-muted">Kapitel</h3>
					<ol class="mt-3 space-y-1">
						{#each media.chapters as ch (ch.id)}
							<li class="flex justify-between rounded-[var(--radius-sm)] px-2 py-2 text-body hover:bg-surface-muted">
								<span>{ch.title ?? `Kapitel ${ch.index + 1}`}</span>
								<span class="text-caption text-ink-muted"
									>{formatDuration(ch.duration_seconds)}</span
								>
							</li>
						{/each}
					</ol>
				</section>
			{/if}

			<div class="border-t border-border px-6 py-5">
				<AudienceEditor {mediaId} />
			</div>

			<details class="border-t border-border px-6 py-5">
				<summary class="cursor-pointer text-label uppercase text-ink-muted">Technische Details</summary>
				<dl class="mt-3 space-y-1 text-caption text-ink-muted">
					<div class="flex justify-between"><dt>ID</dt><dd class="font-mono">{media.id.slice(0, 8)}…</dd></div>
					{#each media.sources as source}
						<div class="flex justify-between"><dt>Quelle</dt><dd>{source.display_name}</dd></div>
					{/each}
				</dl>
			</details>
		</div>
	</div>

	<ArtworkSheet
		open={artworkOpen}
		{mediaId}
		title={media.title}
		onclose={() => (artworkOpen = false)}
	/>

	{#if showDelete}
		<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
		<div
			class="fixed inset-0 z-50 flex items-end justify-center bg-ink/25 p-4 sm:items-center"
			role="presentation"
			onclick={(e) => e.target === e.currentTarget && (showDelete = false)}
		>
			<div class="w-full max-w-sm rounded-[var(--radius-xl)] bg-surface p-6 shadow-md-token" role="alertdialog">
				<h3 class="text-title">Aus Mediathek entfernen?</h3>
				<p class="mt-2 text-body text-ink-muted">
					„{media.title}" wird aus AQENO entfernt. Die Dateien auf dem Speicher bleiben erhalten.
				</p>
				<div class="mt-5 flex gap-2">
					<Button variant="secondary" class="flex-1" onclick={() => (showDelete = false)}>Abbrechen</Button>
					<Button class="flex-1" onclick={() => void remove()}>Entfernen</Button>
				</div>
			</div>
		</div>
	{/if}
{/if}
