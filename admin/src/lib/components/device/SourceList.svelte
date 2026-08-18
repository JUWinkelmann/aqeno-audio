<script lang="ts">
	import { createQuery, useQueryClient } from '@tanstack/svelte-query';
	import { apiRequest } from '$lib/api/client';
	import Button from '$lib/components/primitives/Button.svelte';
	import type { components } from '$lib/api/schema';

	type MediaSourceResource = components['schemas']['MediaSourceResource'];

	const queryClient = useQueryClient();

	const sourcesQuery = createQuery(() => ({
		queryKey: ['media-sources'],
		queryFn: () => apiRequest<MediaSourceResource[]>('/media-sources')
	}));

	let scanning = $state(false);

	async function triggerScan() {
		scanning = true;
		try {
			await apiRequest('/library/scans', { method: 'POST' });
			await queryClient.invalidateQueries({ queryKey: ['operations'] });
		} finally {
			scanning = false;
		}
	}
</script>

<div class="space-y-4">
	<div class="flex items-center justify-between">
		<div>
			<h2 class="text-lg font-semibold">Medienquellen</h2>
			<p class="text-sm text-text-secondary">Woher deine Inhalte kommen.</p>
		</div>
		<Button variant="secondary" disabled={scanning} onclick={() => void triggerScan()}>
			{scanning ? 'Scan läuft …' : 'Bibliothek scannen'}
		</Button>
	</div>

	{#if sourcesQuery.isPending}
		<div class="h-24 animate-pulse rounded-card bg-surface-sunken"></div>
	{:else}
		<div class="space-y-3">
			{#each sourcesQuery.data ?? [] as source (source.id)}
				<article class="rounded-card border border-border bg-surface-raised p-4">
					<div class="flex items-center justify-between">
						<div>
							<p class="font-medium">{source.kind === 'local' ? 'Dieser AQENO' : 'Netzwerkquelle'}</p>
							<p class="text-sm text-text-secondary">{source.path}</p>
						</div>
						<span
							class="text-sm font-medium {source.available ? 'text-success' : 'text-warning'}"
						>
							{source.available ? 'Online' : 'Momentan nicht erreichbar'}
						</span>
					</div>
					{#if !source.available}
						<p class="mt-2 text-sm text-text-secondary">
							Deine Mediathek und lokalen Inhalte funktionieren weiterhin.
						</p>
					{/if}
				</article>
			{/each}
		</div>

		<div class="rounded-card border border-dashed border-border p-4 text-sm text-text-secondary">
			<p class="font-medium text-text-primary">Medienquelle hinzufügen</p>
			<p class="mt-1">
				API GAP: NAS-Mount und Verbindungstest sind noch nicht über die API verfügbar. Quellen
				werden derzeit über die Gerätekonfiguration eingerichtet.
			</p>
		</div>
	{/if}
</div>
