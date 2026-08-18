<script lang="ts">
	type Props = {
		name: string;
		size?: 'sm' | 'md';
	};

	let { name, size = 'md' }: Props = $props();

	const initial = $derived(name.charAt(0).toUpperCase());
	const sizes = { sm: 'h-8 w-8 text-sm', md: 'h-12 w-12 text-lg' };
</script>

<div
	class="flex shrink-0 items-center justify-center rounded-full bg-accent/15 font-semibold text-accent {sizes[
		size
	]}"
	aria-hidden="true"
>
	{initial}
</div>
