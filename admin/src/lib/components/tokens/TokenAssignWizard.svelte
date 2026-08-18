<script lang="ts">
	import { createQuery, useQueryClient } from '@tanstack/svelte-query';
	import { apiRequest } from '$lib/api/client';
	import { subscribeEvents } from '$lib/events/sse';
	import Button from '$lib/components/primitives/Button.svelte';
	import SearchInput from '$lib/components/primitives/SearchInput.svelte';
	import type { components } from '$lib/api/schema';
	import { Nfc } from '@lucide/svelte';

	type TokenCaptureResponse = components['schemas']['TokenCaptureResponse'];
	type MediaPage = components['schemas']['MediaPage'];

	type Props = {
		open?: boolean;
		onclose?: () => void;
	};

	let { open = false, onclose }: Props = $props();

	const queryClient = useQueryClient();

	let step = $state<1 | 2 | 3>(1);
	let captureId = $state<string | null>(null);
	let capture = $state<TokenCaptureResponse | null>(null);
	let search = $state('');
	let selectedMediaId = $state<string | null>(null);
	let error = $state<string | null>(null);

	const mediaQuery = createQuery(() => ({
		queryKey: ['library', 'picker', search],
		queryFn: () =>
			apiRequest<MediaPage>(`/library/media?limit=20${search ? `&search=${encodeURIComponent(search)}` : ''}`),
		enabled: step === 2
	}));

	$effect(() => {
		if (!open || !captureId) return;
		const unsub = subscribeEvents((event) => {
			if (event.type === 'token.capture_changed') {
				void refreshCapture();
			}
		});
		const interval = setInterval(() => void refreshCapture(), 2000);
		return () => {
			unsub();
			clearInterval(interval);
		};
	});

	async function start() {
		error = null;
		step = 1;
		const result = await apiRequest<TokenCaptureResponse>('/token-captures', { method: 'POST' });
		captureId = result.id;
		capture = result;
	}

	async function refreshCapture() {
		if (!captureId) return;
		capture = await apiRequest<TokenCaptureResponse>(`/token-captures/${captureId}`);
		if (capture.state === 'detected') step = 2;
		if (capture.state === 'assigned') step = 3;
	}

	async function assign() {
		if (!captureId || !selectedMediaId) return;
		await apiRequest(`/token-captures/${captureId}/assignment`, {
			method: 'PUT',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ media_id: selectedMediaId })
		});
		step = 3;
		await queryClient.invalidateQueries({ queryKey: ['tokens'] });
	}

	function reset() {
		step = 1;
		captureId = null;
		capture = null;
		selectedMediaId = null;
		search = '';
		error = null;
	}

	$effect(() => {
		if (open && !captureId) void start();
		if (!open) reset();
	});
</script>

{#if open}
	<div class="fixed inset-0 z-50 flex items-end justify-center bg-black/30 sm:items-center">
		<div class="w-full max-w-lg rounded-t-sheet bg-surface-raised p-5 sm:rounded-card">
			{#if step === 1}
				<div class="text-center">
					<div class="mx-auto mb-4 flex h-24 w-24 items-center justify-center rounded-full bg-accent/10">
						<Nfc size={40} class="text-accent" />
					</div>
					<h2 class="text-xl font-semibold">Token zuordnen</h2>
					<p class="mt-2 text-sm text-text-secondary">
						Halte deine Karte oder Figur an AQENO.
					</p>
					{#if capture?.state === 'waiting'}
						<p class="mt-4 animate-pulse text-sm text-accent">Warte auf Token …</p>
					{/if}
				</div>
			{:else if step === 2}
				<h2 class="text-lg font-semibold">Inhalt wählen</h2>
				<p class="text-sm text-text-secondary">Welcher Inhalt soll gestartet werden?</p>
				<div class="mt-3">
					<SearchInput bind:value={search} />
				</div>
				<div class="mt-3 max-h-48 space-y-1 overflow-y-auto">
					{#each mediaQuery.data?.items ?? [] as item (item.id)}
						<button
							type="button"
							class="w-full rounded-button px-3 py-2 text-left text-sm hover:bg-surface-sunken {selectedMediaId ===
							item.id
								? 'bg-accent/10 text-accent'
								: ''}"
							onclick={() => (selectedMediaId = item.id)}
						>
							{item.title}
						</button>
					{/each}
				</div>
				<Button class="mt-4 w-full" disabled={!selectedMediaId} onclick={() => void assign()}>
					Zuordnen
				</Button>
			{:else}
				<div class="text-center">
					<p class="text-lg font-semibold text-success">Fertig!</p>
					<p class="mt-2 text-sm text-text-secondary">Der Token ist jetzt verbunden.</p>
					<Button class="mt-4" onclick={() => onclose?.()}>Schließen</Button>
				</div>
			{/if}

			{#if error}
				<p class="mt-3 text-sm text-danger">{error}</p>
			{/if}

			{#if step < 3}
				<Button variant="ghost" class="mt-3 w-full" onclick={() => onclose?.()}>Abbrechen</Button>
			{/if}
		</div>
	</div>
{/if}
