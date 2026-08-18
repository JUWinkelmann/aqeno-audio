import { connection } from './connection.svelte';
import { ApiError } from './errors';

type RequestOptions = {
	method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
	body?: BodyInit | null;
	headers?: Record<string, string>;
};

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
	const { method = 'GET', body, headers = {} } = options;
	const url = `${connection.baseUrl}${path.startsWith('/') ? path : `/${path}`}`;

	let response: Response;
	try {
		response = await fetch(url, {
			method,
			body,
			credentials: 'include',
			headers: {
				...(method !== 'GET' && connection.csrfToken
					? { 'X-AQENO-CSRF': connection.csrfToken }
					: {}),
				...headers
			}
		});
	} catch {
		throw new ApiError({
			code: 'network_error',
			message: 'Verbindung zum Gerät fehlgeschlagen.',
			details: null
		});
	}

	if (!response.ok) {
		throw await ApiError.fromResponse(response);
	}

	if (response.status === 204) {
		return undefined as T;
	}

	return (await response.json()) as T;
}

export function artworkUrl(relativePath: string | null | undefined): string | null {
	if (!relativePath) return null;
	if (relativePath.startsWith('http')) return relativePath;
	const origin = connection.baseUrl.replace(/\/api\/v1\/?$/, '');
	return `${origin}${relativePath}`;
}

export async function apiUpload(path: string, file: File): Promise<void> {
	const form = new FormData();
	form.append('file', file);
	await apiRequest(path, {
		method: 'POST',
		body: form
	});
}
