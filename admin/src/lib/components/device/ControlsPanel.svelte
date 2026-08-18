<script lang="ts">
	import { createQuery, useQueryClient } from '@tanstack/svelte-query';
	import { apiRequest } from '$lib/api/client';
	import { userMessageForError } from '$lib/api/errors';
	import Button from '$lib/ui/Button.svelte';

	type Capability = {
		id: string;
		type: 'button' | 'rotary_encoder';
		label: string;
		events: string[];
		illumination: boolean;
	};
	type Action = {
		id: string;
		label: string;
		category: string;
		compatible_events: string[];
	};
	type Mapping = {
		control_id: string;
		event: string;
		action_id: string | null;
		supported: boolean;
	};
	type Controls = {
		controls: Capability[];
		actions: Action[];
		mappings: Mapping[];
		illumination: 'off' | 'subtle' | 'clear';
	};

	const queryClient = useQueryClient();
	const query = createQuery(() => ({
		queryKey: ['controls'],
		queryFn: () => apiRequest<Controls>('/controls')
	}));
	let message = $state<string | null>(null);
	let error = $state<string | null>(null);
	let saving = $state<string | null>(null);

	const eventLabels: Record<string, string> = {
		short_press: 'Kurz drücken',
		long_press: 'Lang drücken',
		rotate_left: 'Nach links drehen',
		rotate_right: 'Nach rechts drehen'
	};
	// Categories are listed rather than derived so their order stays deliberate.
	// Anything the API reports outside this list would silently disappear from
	// the select, so a new AQENO action category has to be added here too.
	const actionCategories = [
		{ id: 'playback', label: 'Wiedergabe' },
		{ id: 'volume', label: 'Lautstärke' },
		{ id: 'navigation', label: 'Navigation' },
		{ id: 'display', label: 'Display' }
	];

	function mapping(controlId: string, event: string): Mapping | undefined {
		return query.data?.mappings.find(
			(item) => item.control_id === controlId && item.event === event
		);
	}

	function actionsFor(event: string): Action[] {
		return query.data?.actions.filter((action) => action.compatible_events.includes(event)) ?? [];
	}

	function actionsForCategory(event: string, category: string): Action[] {
		return actionsFor(event).filter((action) => action.category === category);
	}

	async function saveMapping(controlId: string, event: string, actionId: string) {
		saving = `${controlId}:${event}`;
		error = null;
		message = null;
		try {
			const updated = await apiRequest<Controls>(`/controls/${controlId}/mappings/${event}`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ action_id: actionId || null })
			});
			queryClient.setQueryData(['controls'], updated);
			message = 'Belegung gespeichert.';
		} catch (reason) {
			error = userMessageForError(reason);
		} finally {
			saving = null;
		}
	}

	async function saveIllumination(value: Controls['illumination']) {
		saving = 'illumination';
		error = null;
		try {
			const updated = await apiRequest<Controls>('/controls/illumination', {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ illumination: value })
			});
			queryClient.setQueryData(['controls'], updated);
			message = 'Beleuchtung gespeichert.';
		} catch (reason) {
			error = userMessageForError(reason);
		} finally {
			saving = null;
		}
	}

	async function reset() {
		saving = 'reset';
		error = null;
		try {
			const updated = await apiRequest<Controls>('/controls/reset', { method: 'POST' });
			queryClient.setQueryData(['controls'], updated);
			message = 'Standardbelegung wiederhergestellt.';
		} catch (reason) {
			error = userMessageForError(reason);
		} finally {
			saving = null;
		}
	}
</script>

<div class="space-y-6">
	<header>
		<h2 class="text-title">Bedienung</h2>
		<p class="mt-1 text-caption text-ink-muted">
			Lege fest, was die Bedienelemente an diesem AQENO tun.
		</p>
	</header>

	{#if query.isPending}
		<p class="text-body text-ink-muted">Bedienung wird geladen …</p>
	{:else if query.error}
		<p class="text-body text-danger" role="alert">{userMessageForError(query.error)}</p>
	{:else if query.data}
		<div class="grid gap-4 lg:grid-cols-3">
			{#each query.data.controls as control (control.id)}
				<section class="rounded-[var(--radius-xl)] border border-border bg-surface p-5 shadow-sm">
					<div class="mb-5 flex items-center gap-3">
						<span class="grid h-12 w-12 place-items-center rounded-full bg-accent-soft text-title text-accent" aria-hidden="true">
							{control.type === 'rotary_encoder' ? '◉' : control.id === 'primary_left' ? '‹' : '›'}
						</span>
						<h3 class="text-title">{control.label}</h3>
					</div>
					<div class="space-y-4">
						{#each control.events as event (`${control.id}:${event}`)}
							<label class="grid gap-1.5 text-caption font-medium">
								{eventLabels[event] ?? event}
								<select
									class="min-h-12 w-full rounded-[var(--radius-md)] border border-border bg-surface-muted px-3 text-body font-normal"
									value={mapping(control.id, event)?.action_id ?? ''}
									disabled={saving === `${control.id}:${event}`}
									onchange={(change) => void saveMapping(control.id, event, change.currentTarget.value)}
								>
									<option value="">Nicht belegt</option>
									{#if mapping(control.id, event)?.supported === false}
										<option value={mapping(control.id, event)?.action_id ?? ''}>Von dieser Version nicht unterstützt</option>
									{/if}
									{#each actionCategories as category (category.id)}
										{#if actionsForCategory(event, category.id).length}
											<optgroup label={category.label}>
												{#each actionsForCategory(event, category.id) as action (action.id)}
													<option value={action.id}>{action.label}</option>
												{/each}
											</optgroup>
										{/if}
									{/each}
								</select>
							</label>
						{/each}
					</div>
				</section>
			{/each}
		</div>

		<section class="rounded-[var(--radius-xl)] border border-border bg-surface p-5 shadow-sm">
			<h3 class="text-title">Tastenbeleuchtung</h3>
			<p class="mt-1 text-caption text-ink-muted">
				Nachts und bei ausgeschaltetem Display bleibt die Beleuchtung immer aus.
			</p>
			<div class="mt-4 flex flex-wrap gap-2" role="group" aria-label="Tastenbeleuchtung">
				{#each [['off', 'Aus'], ['subtle', 'Dezent'], ['clear', 'Deutlich']] as option (option[0])}
					<button
						type="button"
						class="min-h-12 rounded-full px-5 text-caption font-medium {query.data.illumination === option[0] ? 'bg-accent text-white' : 'bg-surface-muted text-ink'}"
						disabled={saving === 'illumination'}
						onclick={() => void saveIllumination(option[0] as Controls['illumination'])}
					>{option[1]}</button>
				{/each}
			</div>
		</section>

		<div><Button variant="ghost" disabled={saving === 'reset'} onclick={() => void reset()}>Standardbelegung wiederherstellen</Button></div>
		{#if error}<p class="text-caption text-danger" role="alert">{error}</p>{/if}
		{#if message}<p class="text-caption text-success" role="status">{message}</p>{/if}
	{/if}
</div>
