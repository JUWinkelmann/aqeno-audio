<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLButtonAttributes } from 'svelte/elements';

	type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';

	type Props = HTMLButtonAttributes & {
		variant?: Variant;
		children: Snippet;
	};

	let { variant = 'primary', class: className = '', children, ...rest }: Props = $props();

	const variants: Record<Variant, string> = {
		primary:
			'bg-accent text-white hover:bg-accent-hover disabled:opacity-50',
		secondary:
			'bg-surface-sunken text-text-primary hover:bg-border disabled:opacity-50',
		ghost: 'text-text-secondary hover:bg-surface-sunken disabled:opacity-50',
		danger: 'bg-danger text-white hover:opacity-90 disabled:opacity-50'
	};
</script>

<button
	class="inline-flex min-h-11 items-center justify-center gap-2 rounded-button px-4 py-2 text-sm font-medium transition-colors duration-(--duration-fast) ease-(--ease-standard) {variants[
		variant
	]} {className}"
	{...rest}
>
	{@render children()}
</button>
