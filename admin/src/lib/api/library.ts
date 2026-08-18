import type { LibraryFilter } from '$lib/utils/kinds';
import type { ContentKind } from '$lib/utils/kinds';

export type LibraryQueryParams = {
	limit?: number;
	cursor?: string | null;
	search?: string;
	kind?: ContentKind;
	available?: boolean;
	profile_name?: string;
};

export function buildLibraryPath(params: LibraryQueryParams): string {
	const query = new URLSearchParams();
	query.set('limit', String(params.limit ?? 50));
	if (params.cursor) query.set('cursor', params.cursor);
	if (params.search?.trim()) query.set('search', params.search.trim());
	if (params.kind) query.set('kind', params.kind);
	if (params.available != null) query.set('available', String(params.available));
	if (params.profile_name) query.set('profile_name', params.profile_name);
	return `/library/media?${query.toString()}`;
}

export function filterToQueryParams(
	filter: LibraryFilter,
	search: string,
	profileName: string | null
): Omit<LibraryQueryParams, 'cursor'> {
	const base: Omit<LibraryQueryParams, 'cursor'> = {
		limit: 50,
		search: search || undefined,
		profile_name: profileName ?? undefined
	};
	if (filter.type === 'all') return base;
	if (filter.type === 'unavailable') return { ...base, available: false };
	return { ...base, kind: filter.kind };
}
