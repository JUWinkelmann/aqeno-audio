<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { createInfiniteQuery } from '@tanstack/svelte-query';
	import { apiRequest } from '$lib/api/client';
	import { buildLibraryPath, filterToQueryParams } from '$lib/api/library';
	import MediaTile from '$lib/ui/MediaTile.svelte';
	import MediaDetailView from '$lib/ui/MediaDetailView.svelte';
	import TokenAssignWizard from '$lib/components/tokens/TokenAssignWizard.svelte';
	import { importStore } from '$lib/stores/import.svelte';
	import { selection } from '$lib/stores/selection.svelte';
	import { uploadManager } from '$lib/upload/manager.svelte';
	import { FILTER_CHIPS, type LibraryFilter } from '$lib/utils/kinds';
	import { Search } from '@lucide/svelte';
	import type { components } from '$lib/api/schema';

	type MediaPage = components['schemas']['MediaPage'];
	let filter = $state<LibraryFilter>({ type: 'all' });
	let search = $state('');
	let searchInput = $state('');
	let tokenOpen = $state(false);
	let dragging = $state(false);

	const selectedId = $derived(page.url.searchParams.get('id'));

	const queryParams = $derived(filterToQueryParams(filter, search, null));

	const libraryQuery = createInfiniteQuery(() => ({
		queryKey: ['library', queryParams],
		queryFn: ({ pageParam }) =>
			apiRequest<MediaPage>(
				buildLibraryPath({ ...queryParams, cursor: pageParam as string | undefined })
			),
		initialPageParam: undefined as string | undefined,
		getNextPageParam: (last) => last.next_cursor ?? undefined
	}));

	const items = $derived(libraryQuery.data?.pages.flatMap((p) => p.items) ?? []);
	const total = $derived(libraryQuery.data?.pages[0]?.total ?? 0);

	let debounce: ReturnType<typeof setTimeout>;
	function onSearchInput() {
		clearTimeout(debounce);
		debounce = setTimeout(() => (search = searchInput), 250);
	}

	function openMedia(id: string) {
		const url = new URL(page.url);
		url.searchParams.set('id', id);
		void goto(`${url.pathname}?${url.searchParams}`, { keepFocus: true, noScroll: true });
	}

	function closeDetail() {
		void goto('/library', { keepFocus: true });
	}

	let sentinel: HTMLDivElement | undefined = $state();
	$effect(() => {
		if (!sentinel) return;
		const obs = new IntersectionObserver(([e]) => {
			if (e?.isIntersecting && libraryQuery.hasNextPage && !libraryQuery.isFetchingNextPage) {
				void libraryQuery.fetchNextPage();
			}
		}, { rootMargin: '300px' });
		obs.observe(sentinel);
		return () => obs.disconnect();
	});
</script>

<svelte:window
	ondragenter={(e) => e.dataTransfer?.types.includes('Files') && (dragging = true)}
	ondragleave={(e) => e.relatedTarget === null && (dragging = false)}
	ondrop={(e) => {
		dragging = false;
		if (e.dataTransfer?.files.length) {
			uploadManager.addFiles(e.dataTransfer.files);
			importStore.show();
		}
	}}
/>

{#if dragging}
	<div
		class="pointer-events-none fixed inset-4 z-50 flex items-center justify-center rounded-[var(--radius-xl)] border-2 border-dashed border-accent bg-accent-soft/80"
	>
		<p class="text-title text-accent">Dateien hier ablegen</p>
	</div>
{/if}

<div class="flex min-h-[calc(100dvh-4rem)] lg:min-h-dvh">
	<div class="min-w-0 flex-1 px-4 py-6 lg:px-8 lg:py-8">
		<header class="mb-6">
			<h1 class="text-display">Mediathek</h1>
			{#if total > 0}
				<p class="mt-1 text-caption text-ink-muted">{total.toLocaleString('de-DE')} Inhalte</p>
			{/if}
		</header>

		<div class="relative mb-4">
			<Search size={18} class="absolute top-1/2 left-3 -translate-y-1/2 text-ink-faint" />
			<input
				type="search"
				placeholder="Suchen …"
				class="w-full rounded-full border border-border bg-surface py-3 pr-4 pl-10 text-body shadow-sm outline-none focus:border-accent"
				bind:value={searchInput}
				oninput={onSearchInput}
			/>
		</div>

		<div class="mb-5 flex gap-2 overflow-x-auto pb-1">
			{#each FILTER_CHIPS as chip (chip.id)}
				<button
					type="button"
					class="shrink-0 rounded-full px-4 py-2 text-caption font-medium transition-colors {filter.type ===
						chip.filter.type &&
					(filter.type !== 'kind' ||
						(chip.filter.type === 'kind' &&
							filter.type === 'kind' &&
							filter.kind === chip.filter.kind))
						? 'bg-accent-soft text-accent'
						: 'bg-surface text-ink-muted hover:bg-surface-muted'}"
					onclick={() => (filter = chip.filter)}
				>
					{chip.label}
				</button>
			{/each}
		</div>

		{#if libraryQuery.isPending}
			<div class="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-4">
				{#each Array(8) as _, i (i)}
					<div class="aspect-square animate-pulse rounded-[var(--radius-lg)] bg-surface-muted"></div>
				{/each}
			</div>
		{:else if items.length === 0}
			<div class="rounded-[var(--radius-xl)] border border-dashed border-border bg-surface px-6 py-16 text-center">
				<p class="text-title">Deine Mediathek ist noch leer</p>
				<p class="mt-2 text-body text-ink-muted">
					Zieh Hörspiele oder Musik hierher — AQENO erledigt den Rest.
				</p>
				<button type="button" class="mt-6 text-accent" onclick={() => importStore.show()}>
					Inhalte hinzufügen
				</button>
			</div>
		{:else}
			<div class="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-4">
				{#each items as item (item.id)}
					<MediaTile
						{item}
						selected={selection.has(item.id)}
						selectable={selection.active}
						onselect={() => selection.toggle(item.id)}
						onopen={() => openMedia(item.id)}
					/>
				{/each}
			</div>
			<div bind:this={sentinel} class="h-8"></div>
		{/if}
	</div>

	{#if selectedId}
		<aside class="hidden w-[26rem] shrink-0 border-l border-border bg-canvas p-4 lg:block">
			<MediaDetailView
				mediaId={selectedId}
				onclose={closeDetail}
				ontag={() => (tokenOpen = true)}
			/>
		</aside>
	{/if}
</div>

{#if selectedId}
	<div class="fixed inset-0 z-50 bg-canvas lg:hidden">
		<MediaDetailView mediaId={selectedId} onclose={closeDetail} ontag={() => (tokenOpen = true)} />
	</div>
{/if}

<TokenAssignWizard open={tokenOpen} onclose={() => (tokenOpen = false)} />
