<script lang="ts">
	import type { components } from '$lib/api/schema';
	import { kindLabel } from '$lib/utils/kinds';
	import { ImagePlus } from '@lucide/svelte';

	type ContentKind = components['schemas']['ContentKind'];

	type Props = {
		title: string;
		kind?: ContentKind;
		src?: string | null;
		hue?: number;
		size?: 'sm' | 'md' | 'lg' | 'hero';
		editable?: boolean;
		onedit?: () => void;
	};

	let {
		title,
		kind,
		src = null,
		hue = 28,
		size = 'md',
		editable = false,
		onedit
	}: Props = $props();

	const initial = $derived(title.charAt(0).toUpperCase());
	const sizes = {
		sm: 'h-12 w-12 text-lg rounded-[var(--radius-sm)]',
		md: 'h-full w-full text-4xl rounded-[var(--radius-md)]',
		lg: 'h-full w-full text-5xl rounded-[var(--radius-lg)]',
		hero: 'h-full w-full text-6xl rounded-[var(--radius-xl)]'
	};
</script>

<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<div
	class="group relative overflow-hidden bg-surface-muted {sizes[size]} {editable
		? 'cursor-pointer'
		: ''}"
	style={!src ? `--placeholder-hue: ${hue}` : undefined}
	role={editable ? 'button' : undefined}
	tabindex={editable ? 0 : undefined}
	onclick={() => editable && onedit?.()}
	onkeydown={(e) => editable && e.key === 'Enter' && onedit?.()}
>
	{#if src}
		<img {src} alt="" class="h-full w-full object-cover" loading="lazy" decoding="async" />
	{:else}
		<div
			class="flex h-full w-full flex-col items-center justify-center gap-1"
			style="background: linear-gradient(145deg, hsl(var(--placeholder-hue) 45% 88%), hsl(calc(var(--placeholder-hue) + 20) 35% 78%))"
		>
			<span class="font-semibold text-ink/70">{initial}</span>
			{#if kind && size !== 'sm'}
				<span class="text-caption text-ink-muted">{kindLabel(kind)}</span>
			{/if}
		</div>
	{/if}

	{#if editable}
		<div
			class="absolute inset-0 flex items-center justify-center bg-ink/0 opacity-0 transition-opacity duration-(--duration-fast) group-hover:bg-ink/40 group-hover:opacity-100 group-focus-visible:bg-ink/40 group-focus-visible:opacity-100"
		>
			<span class="flex items-center gap-1.5 rounded-full bg-surface px-3 py-1.5 text-caption font-medium shadow-sm">
				<ImagePlus size={14} />
				Cover ändern
			</span>
		</div>
	{/if}
</div>

<style>
	.text-caption {
		font-size: 0.75rem;
	}
</style>
