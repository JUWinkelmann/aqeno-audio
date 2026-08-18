const STORAGE_KEY = 'aqeno-admin-connection';

const DEFAULT_BASE_URL = (() => {
	if (typeof window === 'undefined') return '/api/v1';
	return `${window.location.origin}/api/v1`;
})();

export type ConnectionConfig = {
	baseUrl: string;
	csrfToken: string;
	deviceName: string | null;
};

function loadStored(): Partial<ConnectionConfig> {
	if (typeof sessionStorage === 'undefined') return {};
	try {
		const raw = sessionStorage.getItem(STORAGE_KEY);
		return raw ? (JSON.parse(raw) as Partial<ConnectionConfig>) : {};
	} catch {
		return {};
	}
}

function persist(config: ConnectionConfig) {
	if (typeof sessionStorage === 'undefined') return;
	sessionStorage.setItem(STORAGE_KEY, JSON.stringify(config));
}

class ConnectionState {
	baseUrl = $state(DEFAULT_BASE_URL);
	csrfToken = $state('');
	deviceName = $state<string | null>(null);

	constructor() {
		const stored = loadStored();
		if (stored.baseUrl) this.baseUrl = stored.baseUrl;
		if (stored.csrfToken) this.csrfToken = stored.csrfToken;
		if (stored.deviceName) this.deviceName = stored.deviceName;
	}

	get isConnected(): boolean {
		return Boolean(this.csrfToken && this.deviceName);
	}

	connect(baseUrl: string, csrfToken: string, deviceName: string) {
		this.baseUrl = baseUrl.replace(/\/$/, '');
		this.csrfToken = csrfToken;
		this.deviceName = deviceName;
		persist({ baseUrl: this.baseUrl, csrfToken: this.csrfToken, deviceName: this.deviceName });
	}

	disconnect() {
		this.csrfToken = '';
		this.deviceName = null;
		if (typeof sessionStorage !== 'undefined') sessionStorage.removeItem(STORAGE_KEY);
	}
}

export const connection = new ConnectionState();
