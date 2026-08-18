<script lang="ts">
	type Props = {
		value?: string;
		placeholder?: string;
		oninput?: (value: string) => void;
	};

	let { value = $bindable(''), placeholder = 'Suchen …', oninput }: Props = $props();
</script>

<input
	type="search"
	class="w-full rounded-button border border-border bg-surface-sunken px-3 py-2.5 text-sm outline-none focus:border-accent"
	{placeholder}
	bind:value
	oninput={() => oninput?.(value)}
/>
