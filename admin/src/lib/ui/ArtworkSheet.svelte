<script lang="ts">
	import { useQueryClient } from '@tanstack/svelte-query';
	import { apiRequest } from '$lib/api/client';
	import Button from '$lib/ui/Button.svelte';
	import Sheet from '$lib/ui/Sheet.svelte';
	import { Camera, Image, Search, Trash2 } from '@lucide/svelte';

	type Props = {
		open?: boolean;
		mediaId: string;
		title: string;
		onclose?: () => void;
	};

	let { open = false, mediaId, title, onclose }: Props = $props();

	const queryClient = useQueryClient();
	let uploading = $state(false);
	let error = $state<string | null>(null);

	async function uploadFile(file: File) {
		uploading = true;
		error = null;
		try {
			const form = new FormData();
			form.append('file', file);
			await apiRequest(`/library/media/${mediaId}/artwork`, {
				method: 'PUT',
				body: form
			});
			await queryClient.invalidateQueries({ queryKey: ['media', mediaId] });
			await queryClient.invalidateQueries({ queryKey: ['library'] });
			onclose?.();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Speichern fehlgeschlagen';
		} finally {
			uploading = false;
		}
	}

	function onPick(event: Event) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (file) void uploadFile(file);
		input.value = '';
	}

	async function remove() {
		await apiRequest(`/library/media/${mediaId}/artwork`, { method: 'DELETE' });
		await queryClient.invalidateQueries({ queryKey: ['media', mediaId] });
		onclose?.();
	}
</script>

<Sheet {open} title="Cover ändern" {onclose}>
	<p class="mb-4 text-caption text-ink-muted">{title}</p>

	<div class="space-y-2">
		<label
			class="flex cursor-pointer items-center gap-4 rounded-[var(--radius-md)] border border-border p-4 hover:bg-surface-muted"
		>
			<input type="file" class="hidden" accept="image/*" capture="environment" onchange={onPick} />
			<Camera size={22} class="text-accent" />
			<div>
				<p class="text-body font-medium">Foto aufnehmen</p>
				<p class="text-caption text-ink-muted">Cover vom Hörspiel fotografieren</p>
			</div>
		</label>

		<label
			class="flex cursor-pointer items-center gap-4 rounded-[var(--radius-md)] border border-border p-4 hover:bg-surface-muted"
		>
			<input type="file" class="hidden" accept="image/*" onchange={onPick} />
			<Image size={22} class="text-accent" />
			<div>
				<p class="text-body font-medium">Bild auswählen</p>
				<p class="text-caption text-ink-muted">Aus Fotos oder Dateien</p>
			</div>
		</label>

		<div
			class="flex items-center gap-4 rounded-[var(--radius-md)] border border-dashed border-border p-4 opacity-50"
		>
			<Search size={22} />
			<div>
				<p class="text-body font-medium">Cover suchen</p>
				<p class="text-caption text-ink-muted">Demnächst — Backend-Erweiterung nötig</p>
			</div>
		</div>

		<button
			type="button"
			class="flex w-full items-center gap-4 rounded-[var(--radius-md)] p-4 text-danger hover:bg-surface-muted"
			onclick={() => void remove()}
		>
			<Trash2 size={22} />
			<span class="text-body font-medium">Cover entfernen</span>
		</button>
	</div>

	{#if uploading}
		<p class="mt-4 text-center text-caption text-ink-muted">Wird gespeichert …</p>
	{/if}
	{#if error}
		<p class="mt-2 text-center text-caption text-danger">{error}</p>
	{/if}
</Sheet>
