export function formatDuration(seconds: number | null | undefined): string {
	if (seconds == null || seconds <= 0) return '—';
	const total = Math.round(seconds);
	const h = Math.floor(total / 3600);
	const m = Math.floor((total % 3600) / 60);
	if (h > 0) return `${h} Std ${m} Min`;
	return `${m} Min`;
}

export function formatBytes(bytes: number): string {
	if (bytes < 1024 ** 2) return `${Math.round(bytes / 1024)} KB`;
	if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
	return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
}

export function formatProgress(position: number | null, duration: number | null): string {
	if (position == null || duration == null || duration <= 0) return '';
	const pct = Math.round((position / duration) * 100);
	return `${pct} %`;
}
