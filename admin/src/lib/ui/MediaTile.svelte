<script lang="ts">
	import { artworkUrl } from '$lib/api/client';
	import { kindLabel } from '$lib/utils/kinds';
	import Artwork from '$lib/ui/Artwork.svelte';
	import type { components } from '$lib/api/schema';
	import { formatDuration } from '$lib/utils/format';

	type MediaSummary = components['schemas']['MediaSummary'];

	type Props = {
		item: MediaSummary;
		selected?: boolean;
		selectable?: boolean;
		onselect?: () => void;
		onopen?: () => void;
	};

	let { item, selected = false, selectable = false, onselect, onopen }: Props = $props();

	const thumb = $derived(artworkUrl(item.artwork_thumbnail_url));
	const hue = $derived((item.title.charCodeAt(0) * 17) % 360);
</script>

<article
	class="group flex flex-col overflow-hidden rounded-[var(--radius-lg)] bg-surface transition-shadow hover:shadow-md-token {selected
		? 'ring-2 ring-accent ring-offset-2 ring-offset-canvas'
		: ''}"
>
	<button
		type="button"
		class="relative aspect-square w-full overflow-hidden text-left"
		onclick={() => onopen?.()}
	>
		{#if selectable}
			<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
			<div
				class="absolute top-3 left-3 z-10 flex h-7 w-7 items-center justify-center rounded-full border-2 bg-surface text-sm shadow-sm {selected
					? 'border-accent text-accent'
					: 'border-border'}"
				role="checkbox"
				tabindex="0"
				aria-checked={selected}
				onclick={(e) => {
					e.stopPropagation();
					onselect?.();
				}}
			>
				{selected ? '✓' : ''}
			</div>
		{/if}

		<Artwork
			title={item.title}
			kind={item.kind}
			src={thumb}
			{hue}
			size="md"
		/>

		{#if !item.available}
			<span
				class="absolute right-3 bottom-3 rounded-full bg-attention-soft px-2 py-0.5 text-label text-attention"
			>
				Nicht erreichbar
			</span>
		{/if}
	</button>

	<div class="space-y-0.5 p-3">
		<h3 class="line-clamp-2 text-body font-medium leading-snug">{item.title}</h3>
		<p class="text-caption text-ink-muted">
			{kindLabel(item.kind)}
			{#if item.duration_seconds}
				· {formatDuration(item.duration_seconds)}
			{/if}
		</p>
	</div>
</article>
