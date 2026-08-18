<script lang="ts">
	import { uploadManager } from '$lib/upload/manager.svelte';
	import Button from '$lib/ui/Button.svelte';
	import Sheet from '$lib/ui/Sheet.svelte';
	import { Check, Circle, LoaderCircle } from '@lucide/svelte';

	type Props = {
		open?: boolean;
		onclose?: () => void;
	};

	let { open = false, onclose }: Props = $props();

	type Step = { label: string; state: 'done' | 'active' | 'pending' };

	let steps = $state<Step[]>([
		{ label: 'Dateien werden hochgeladen', state: 'active' },
		{ label: 'AQENO analysiert die Dateien', state: 'pending' },
		{ label: 'Zusammengehöriges wird erkannt', state: 'pending' },
		{ label: 'Metadaten und Cover werden übernommen', state: 'pending' }
	]);

	let fileCount = $derived(
		uploadManager.groups.reduce((sum, g) => sum + g.files.length, 0) || 0
	);

	$effect(() => {
		if (!open) return;
		const allDone = uploadManager.groups.every((g) =>
			g.files.every((f) => f.status === 'complete' || f.status === 'processing')
		);
		if (allDone && fileCount > 0) {
			steps = [
				{ label: `${fileCount} Dateien hochgeladen`, state: 'done' },
				{ label: 'AQENO hat die Bibliothek aktualisiert', state: 'done' },
				{
					label: 'Einzelergebnisse — nach Import in der Mediathek sichtbar',
					state: 'done'
				},
				{
					label: 'Unsichere Zuordnungen erscheinen unter Prüfen',
					state: fileCount > 0 ? 'active' : 'pending'
				}
			];
		}
	});

	function onFileInput(event: Event) {
		const input = event.target as HTMLInputElement;
		if (input.files?.length) {
			uploadManager.addFiles(input.files);
			steps[0].state = 'active';
		}
		input.value = '';
	}
</script>

<Sheet {open} title="Inhalte hinzufügen" {onclose}>
	{#if fileCount === 0}
		<div
			class="flex flex-col items-center rounded-[var(--radius-xl)] border-2 border-dashed border-border bg-canvas px-6 py-12 text-center"
		>
			<p class="text-title">Dateien hierher ziehen</p>
			<p class="mt-2 max-w-xs text-caption text-ink-muted">
				Musik, Hörspiele, Hörbücher — AQENO erkennt Kapitel, Titel und Cover.
			</p>
			<label class="mt-6">
				<input type="file" class="hidden" multiple accept="audio/*" onchange={onFileInput} />
				<Button>Dateien auswählen</Button>
			</label>
		</div>

		<p class="mt-6 text-center text-caption text-ink-faint">
			Oder einen
			<a href="/aqeno?section=storage" class="text-accent" onclick={() => onclose?.()}>Speicherort</a>
			verbinden
		</p>
	{:else}
		<p class="mb-4 text-body text-ink-muted">
			{fileCount} {fileCount === 1 ? 'Datei' : 'Dateien'} werden verarbeitet
		</p>

		<ol class="space-y-3">
			{#each steps as step, i (i)}
				<li class="flex items-start gap-3">
					<span class="mt-0.5 shrink-0">
						{#if step.state === 'done'}
							<Check size={18} class="text-success" />
						{:else if step.state === 'active'}
							<LoaderCircle size={18} class="animate-spin text-accent" />
						{:else}
							<Circle size={18} class="text-ink-faint" />
						{/if}
					</span>
					<span
						class="text-body {step.state === 'pending'
							? 'text-ink-faint'
							: step.state === 'active'
								? 'text-ink font-medium'
								: 'text-ink-muted'}"
					>
						{step.label}
					</span>
				</li>
			{/each}
		</ol>

		{#each uploadManager.groups as group (group.id)}
			<div class="mt-4 rounded-[var(--radius-md)] bg-surface-muted p-3">
				<p class="text-caption font-medium">{group.label}</p>
				<p class="text-label text-ink-muted">{group.files.length} Dateien</p>
			</div>
		{/each}

		<div class="mt-6 flex gap-2">
			<Button variant="secondary" class="flex-1" onclick={() => onclose?.()}>Im Hintergrund weiter</Button>
			<a href="/library" class="flex-1" onclick={() => onclose?.()}>
				<Button class="w-full">Zur Mediathek</Button>
			</a>
		</div>
	{/if}
</Sheet>
