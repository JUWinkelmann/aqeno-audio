class SelectionState {
	active = $state(false);
	ids = $state<Set<string>>(new Set());

	get count(): number {
		return this.ids.size;
	}

	toggle(id: string) {
		const next = new Set(this.ids);
		if (next.has(id)) next.delete(id);
		else next.add(id);
		this.ids = next;
	}

	select(id: string) {
		this.ids = new Set([id]);
	}

	add(id: string) {
		const next = new Set(this.ids);
		next.add(id);
		this.ids = next;
	}

	clear() {
		this.ids = new Set();
		this.active = false;
	}

	start() {
		this.active = true;
	}

	has(id: string): boolean {
		return this.ids.has(id);
	}
}

export const selection = new SelectionState();
