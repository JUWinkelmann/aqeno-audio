<script lang="ts">
	import type { Snippet } from 'svelte';

	type Variant = 'primary' | 'secondary' | 'ghost' | 'soft';

	type Props = {
		variant?: Variant;
		class?: string;
		type?: 'button' | 'submit';
		disabled?: boolean;
		onclick?: () => void;
		children: Snippet;
	};

	let {
		variant = 'primary',
		class: className = '',
		type = 'button',
		disabled = false,
		onclick,
		children
	}: Props = $props();

	const styles: Record<Variant, string> = {
		primary: 'bg-accent text-white hover:opacity-90',
		secondary: 'bg-surface text-ink border border-border hover:bg-surface-muted',
		ghost: 'text-ink-muted hover:bg-surface-muted hover:text-ink',
		soft: 'bg-accent-soft text-accent hover:bg-accent-soft/80'
	};
</script>

<button
	{type}
	{disabled}
	class="inline-flex min-h-12 items-center justify-center gap-2 rounded-full px-5 text-sm font-medium transition-all duration-(--duration-fast) disabled:opacity-40 {styles[
		variant
	]} {className}"
	{onclick}
>
	{@render children()}
</button>
