<script lang="ts">
	import { connection } from '$lib/api/connection.svelte';
	import ConnectScreen from '$lib/components/shell/ConnectScreen.svelte';
	import Shell from '$lib/ui/Shell.svelte';
	import ImportSheet from '$lib/ui/ImportSheet.svelte';
	import { subscribeEvents } from '$lib/events/sse';
	import { importStore } from '$lib/stores/import.svelte';
	import { uploadManager } from '$lib/upload/manager.svelte';
	import { useQueryClient } from '@tanstack/svelte-query';
	import type { Snippet } from 'svelte';

	type Props = { children: Snippet };

	let { children }: Props = $props();
	const queryClient = useQueryClient();

	$effect(() => {
		if (!connection.isConnected) return;
		return subscribeEvents((event) => {
			if (event.type === 'operation.changed') {
				void queryClient.invalidateQueries({ queryKey: ['operations'] });
				void queryClient.invalidateQueries({ queryKey: ['library'] });
				uploadManager.markProcessingComplete();
			}
			if (event.type === 'token.capture_changed') {
				void queryClient.invalidateQueries({ queryKey: ['tags'] });
			}
			if (event.type === 'playback.changed') {
				void queryClient.invalidateQueries({ queryKey: ['playback'] });
			}
		});
	});
</script>

{#if connection.isConnected}
	<Shell onadd={() => importStore.show()}>
		{@render children()}
	</Shell>
	<ImportSheet open={importStore.open} onclose={() => importStore.close()} />
{:else}
	<ConnectScreen />
{/if}
