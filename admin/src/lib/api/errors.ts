import type { components } from './schema';

export type ApiErrorBody = components['schemas']['ErrorBody'];

export class ApiError extends Error {
	readonly code: string;
	readonly details: Record<string, unknown> | null;

	constructor(body: ApiErrorBody) {
		super(body.message);
		this.name = 'ApiError';
		this.code = body.code;
		this.details = (body.details as Record<string, unknown> | null) ?? null;
	}

	static async fromResponse(response: Response): Promise<ApiError> {
		try {
			const payload = (await response.json()) as { error?: ApiErrorBody };
			if (payload.error) {
				return new ApiError(payload.error);
			}
		} catch {
			// fall through
		}
		return new ApiError({
			code: 'request_failed',
			message: `Anfrage fehlgeschlagen (${response.status})`,
			details: null
		});
	}
}

const USER_MESSAGES: Record<string, string> = {
	authentication_required: 'Bitte melde dich erneut an.',
	password_incorrect: 'Das Passwort ist nicht korrekt.',
	password_policy: 'Das Passwort muss mindestens 10 Zeichen lang sein.',
	auth_rate_limited: 'Zu viele Versuche. Bitte versuche es in Kürze erneut.',
	physical_confirmation_required: 'Die Bestätigung ist abgelaufen. Bitte starte sie erneut.',
	setup_state_invalid: 'Die Verwaltung konnte nicht eingerichtet werden. Bitte starte erneut.',
	csrf_required: 'Die Sitzung konnte nicht bestätigt werden. Bitte melde dich erneut an.',
	validation_failed: 'Die Eingabe ist ungültig.',
	media_not_found: 'Dieser Inhalt wurde nicht gefunden.',
	token_not_detected: 'Noch kein Token erkannt. Halte die Karte erneut an AQENO.',
	upload_too_large: 'Die Datei ist zu groß (max. 4 GB).',
	bulk_limit_exceeded: 'Zu viele Einträge auf einmal. Bitte in kleineren Gruppen versuchen.',
	request_failed: 'AQENO ist gerade nicht erreichbar.',
	network_error: 'Verbindung zum Gerät fehlgeschlagen.'
};

export function userMessageForError(error: unknown): string {
	if (error instanceof ApiError) {
		return USER_MESSAGES[error.code] ?? error.message;
	}
	if (error instanceof TypeError) {
		return USER_MESSAGES.network_error;
	}
	return USER_MESSAGES.request_failed;
}
