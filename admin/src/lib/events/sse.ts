import { connection } from '$lib/api/connection.svelte';

export type AqenoEventType = 'operation.changed' | 'token.capture_changed' | 'playback.changed';

export type AqenoEvent = {
	type: AqenoEventType;
	data: Record<string, unknown>;
};

export function subscribeEvents(onEvent: (event: AqenoEvent) => void): () => void {
	const url = `${connection.baseUrl}/events`;
	const source = new EventSource(url, {
		withCredentials: true
	});

	// EventSource cannot set custom headers; use fetch-based SSE alternative.
	source.close();

	let closed = false;
	const controller = new AbortController();

	void (async () => {
		try {
			const response = await fetch(url, {
				credentials: 'include',
				signal: controller.signal
			});
			if (!response.ok || !response.body) return;

			const reader = response.body.getReader();
			const decoder = new TextDecoder();
			let buffer = '';

			while (!closed) {
				const { done, value } = await reader.read();
				if (done) break;
				buffer += decoder.decode(value, { stream: true });
				const parts = buffer.split('\n\n');
				buffer = parts.pop() ?? '';

				for (const part of parts) {
					const lines = part.split('\n');
					let type: AqenoEventType | null = null;
					let data = '{}';
					for (const line of lines) {
						if (line.startsWith('event: ')) type = line.slice(7) as AqenoEventType;
						if (line.startsWith('data: ')) data = line.slice(6);
					}
					if (type) {
						try {
							onEvent({ type, data: JSON.parse(data) as Record<string, unknown> });
						} catch {
							// ignore malformed events
						}
					}
				}
			}
		} catch {
			// connection closed
		}
	})();

	return () => {
		closed = true;
		controller.abort();
	};
}
