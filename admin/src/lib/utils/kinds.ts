import type { components } from '$lib/api/schema';

export type ContentKind = components['schemas']['ContentKind'];

export const KIND_LABELS: Record<ContentKind, string> = {
	audio_drama: 'Hörspiel',
	audiobook: 'Hörbuch',
	music_album: 'Album',
	music_track: 'Titel',
	podcast_episode: 'Podcast',
	radio_stream: 'Radio',
	personal_recording: 'Aufnahme'
};

export type LibraryFilter =
	| { type: 'all' }
	| { type: 'kind'; kind: ContentKind }
	| { type: 'unavailable' };

export const FILTER_CHIPS: { id: string; label: string; filter: LibraryFilter }[] = [
	{ id: 'all', label: 'Alles', filter: { type: 'all' } },
	{ id: 'audio_drama', label: 'Hörspiele', filter: { type: 'kind', kind: 'audio_drama' } },
	{ id: 'audiobook', label: 'Hörbücher', filter: { type: 'kind', kind: 'audiobook' } },
	{ id: 'music_album', label: 'Alben', filter: { type: 'kind', kind: 'music_album' } },
	{ id: 'music_track', label: 'Musiktitel', filter: { type: 'kind', kind: 'music_track' } },
	{ id: 'podcast_episode', label: 'Podcasts', filter: { type: 'kind', kind: 'podcast_episode' } },
	{ id: 'radio_stream', label: 'Radio', filter: { type: 'kind', kind: 'radio_stream' } },
	{ id: 'personal_recording', label: 'Aufnahmen', filter: { type: 'kind', kind: 'personal_recording' } },
	{ id: 'unavailable', label: 'Nicht erreichbar', filter: { type: 'unavailable' } }
];

export function kindLabel(kind: ContentKind): string {
	return KIND_LABELS[kind] ?? kind;
}
