<script lang="ts">
	import { page } from '$app/state';
	import { apiRequest } from '$lib/api/client';
	import { connection } from '$lib/api/connection.svelte';
	import { Plus, Home, Library, Users, Nfc, Radio, LogOut } from '@lucide/svelte';
	import type { Snippet } from 'svelte';

	type Props = {
		children: Snippet;
		onadd?: () => void;
	};

	let { children, onadd }: Props = $props();

	const nav = [
		{ href: '/', label: 'Start', icon: Home },
		{ href: '/library', label: 'Mediathek', icon: Library },
		{ href: '/people', label: 'Personen', icon: Users, desktopOnly: true },
		{ href: '/tags', label: 'Tags', icon: Nfc, desktopOnly: true },
		{ href: '/aqeno', label: 'AQENO', icon: Radio, desktopOnly: true }
	];

	function active(href: string): boolean {
		if (href === '/') return page.url.pathname === '/';
		return page.url.pathname.startsWith(href);
	}

	async function logout() {
		try {
			await apiRequest<void>('/auth/logout', { method: 'POST' });
		} finally {
			connection.disconnect();
		}
	}
</script>

<div class="flex min-h-dvh bg-canvas">
	<!-- Desktop sidebar -->
	<aside class="hidden w-[17rem] shrink-0 flex-col border-r border-border bg-surface lg:flex">
		<div class="px-6 py-7">
			<p class="text-label uppercase text-accent">AQENO</p>
			<p class="mt-1 truncate text-title">{connection.deviceName ?? 'Administration'}</p>
		</div>

		<nav class="flex flex-1 flex-col gap-1 px-3" aria-label="Hauptnavigation">
			{#each nav as item (item.href)}
				<a
					href={item.href}
					class="flex min-h-11 items-center gap-3 rounded-[var(--radius-md)] px-3 text-body font-medium transition-colors {active(
						item.href
					)
						? 'bg-accent-soft text-accent'
						: 'text-ink-muted hover:bg-surface-muted hover:text-ink'}"
					aria-current={active(item.href) ? 'page' : undefined}
				>
					<item.icon size={20} strokeWidth={1.75} />
					<span class="flex-1">{item.label}</span>
				</a>
			{/each}
		</nav>

		<div class="space-y-2 p-4">
			<button
				type="button"
				class="flex min-h-11 w-full items-center justify-center gap-2 rounded-full text-sm font-medium text-ink-muted hover:bg-surface-muted hover:text-ink"
				onclick={() => void logout()}
			>
				<LogOut size={18} />
				Abmelden
			</button>
			<button
				type="button"
				class="flex w-full min-h-12 items-center justify-center gap-2 rounded-full bg-accent text-sm font-medium text-white transition-opacity hover:opacity-90"
				onclick={() => onadd?.()}
			>
				<Plus size={18} />
				Hinzufügen
			</button>
		</div>
	</aside>

	<div class="flex min-w-0 flex-1 flex-col">
		<main class="flex-1 pb-20 lg:pb-0">
			{@render children()}
		</main>

		<!-- Mobile bottom nav -->
		<nav
			class="fixed inset-x-0 bottom-0 z-40 flex border-t border-border bg-surface/95 backdrop-blur-sm lg:hidden"
			aria-label="Mobile Navigation"
		>
			{#each nav.filter((i) => !i.desktopOnly) as item (item.href)}
				<a
					href={item.href}
					class="relative flex min-h-16 flex-1 flex-col items-center justify-center gap-0.5 text-label {active(
						item.href
					)
						? 'text-accent'
						: 'text-ink-muted'}"
				>
					<item.icon size={22} strokeWidth={1.75} />
					{item.label}
				</a>
			{/each}
			<a
				href="/people"
				class="flex min-h-16 flex-1 flex-col items-center justify-center gap-0.5 text-label {page.url.pathname.startsWith(
					'/people'
				) ||
				page.url.pathname.startsWith('/tags') ||
				page.url.pathname.startsWith('/aqeno')
					? 'text-accent'
					: 'text-ink-muted'}"
			>
				<Users size={22} strokeWidth={1.75} />
				Mehr
			</a>
		</nav>

		<!-- Mobile FAB -->
		<button
			type="button"
			class="fixed right-4 bottom-20 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-accent text-white shadow-md-token lg:hidden"
			aria-label="Hinzufügen"
			onclick={() => onadd?.()}
		>
			<Plus size={24} />
		</button>
	</div>
</div>
