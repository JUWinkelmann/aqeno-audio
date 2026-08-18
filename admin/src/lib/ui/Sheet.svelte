<script lang="ts">
	import type { Snippet } from 'svelte';
	import { X } from '@lucide/svelte';

	type Props = {
		open?: boolean;
		title?: string;
		onclose?: () => void;
		children: Snippet;
	};

	let { open = false, title, onclose, children }: Props = $props();
</script>

{#if open}
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-end justify-center bg-ink/25 sm:items-center sm:p-4"
		role="presentation"
		onclick={(e) => e.target === e.currentTarget && onclose?.()}
	>
		<div
			class="flex max-h-[92dvh] w-full max-w-lg flex-col rounded-t-[var(--radius-xl)] bg-surface shadow-md sm:rounded-[var(--radius-xl)]"
			role="dialog"
			aria-modal="true"
			aria-label={title}
		>
			{#if title}
				<div class="flex items-center justify-between border-b border-border px-5 py-4">
					<h2 class="text-title font-semibold">{title}</h2>
					<button
						type="button"
						class="rounded-full p-2 text-ink-muted hover:bg-surface-muted"
						aria-label="Schließen"
						onclick={() => onclose?.()}
					>
						<X size={20} />
					</button>
				</div>
			{/if}
			<div class="overflow-y-auto p-5">
				{@render children()}
			</div>
		</div>
	</div>
{/if}

<style>
	.text-title {
		font-size: 1.125rem;
	}
</style>
