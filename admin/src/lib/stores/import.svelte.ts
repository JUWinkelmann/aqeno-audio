class ImportStore {
	open = $state(false);

	show() {
		this.open = true;
	}

	close() {
		this.open = false;
	}
}

export const importStore = new ImportStore();
