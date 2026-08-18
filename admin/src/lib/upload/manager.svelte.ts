import Uppy from '@uppy/core';
import XHRUpload from '@uppy/xhr-upload';
import { connection } from '$lib/api/connection.svelte';
import type { components } from '$lib/api/schema';

type OperationResponse = components['schemas']['OperationResponse'];

export type UploadGroup = {
	id: string;
	label: string;
	files: { id: string; name: string; progress: number; status: string; error?: string }[];
};

class UploadManager {
	groups = $state<UploadGroup[]>([]);
	visible = $state(false);
	private uppy: Uppy | null = null;
	private groupMap = new Map<string, string>();

	init() {
		if (this.uppy) return;
		const uppy = new Uppy({
			autoProceed: true,
			restrictions: { maxNumberOfFiles: null }
		});

		uppy.use(XHRUpload, {
			endpoint: `${connection.baseUrl}/imports`,
			fieldName: 'file',
			method: 'POST',
			withCredentials: true,
			headers: { 'X-AQENO-CSRF': connection.csrfToken },
			getResponseData(xhr: XMLHttpRequest) {
				try {
					return JSON.parse(xhr.responseText) as OperationResponse;
				} catch {
					return {};
				}
			}
		});

		uppy.on('file-added', (file) => {
			const groupKey = inferGroupKey(file.name ?? 'Datei');
			this.groupMap.set(file.id, groupKey);
			this.upsertFile(groupKey, file.id, file.name ?? 'Datei', 0, 'uploading');
			this.visible = true;
		});

		uppy.on('upload-progress', (file, progress) => {
			if (!file) return;
			const groupKey = this.groupMap.get(file.id);
			if (!groupKey) return;
			const pct = progress.bytesTotal
				? Math.round((progress.bytesUploaded / progress.bytesTotal) * 100)
				: 0;
			this.upsertFile(groupKey, file.id, file.name ?? 'Datei', pct, 'uploading');
		});

		uppy.on('upload-success', (file) => {
			if (!file) return;
			const groupKey = this.groupMap.get(file.id);
			if (!groupKey) return;
			this.upsertFile(groupKey, file.id, file.name ?? 'Datei', 100, 'processing');
		});

		uppy.on('upload-error', (file, error) => {
			if (!file) return;
			const groupKey = this.groupMap.get(file.id);
			if (!groupKey) return;
			this.upsertFile(groupKey, file.id, file.name ?? 'Datei', 0, 'error', error.message);
		});

		uppy.on('complete', () => {
			for (const group of this.groups) {
				for (const file of group.files) {
					if (file.status === 'uploading') {
						file.status = 'processing';
						file.progress = 100;
					}
				}
			}
			this.groups = [...this.groups];
		});

		this.uppy = uppy;
	}

	addFiles(files: File[] | FileList) {
		this.init();
		this.uppy?.addFiles(
			Array.from(files).map((file) => ({
				name: file.name,
				type: file.type,
				data: file,
				meta: { relativePath: (file as File & { webkitRelativePath?: string }).webkitRelativePath }
			}))
		);
	}

	private upsertFile(
		groupKey: string,
		fileId: string,
		name: string,
		progress: number,
		status: string,
		error?: string
	) {
		let group = this.groups.find((g) => g.id === groupKey);
		if (!group) {
			group = { id: groupKey, label: groupKey, files: [] };
			this.groups = [...this.groups, group];
		}
		const existing = group.files.find((f) => f.id === fileId);
		if (existing) {
			existing.progress = progress;
			existing.status = status;
			existing.error = error;
		} else {
			group.files.push({ id: fileId, name, progress, status, error });
		}
		this.groups = [...this.groups];
	}

	dismiss() {
		const allDone = this.groups.every((g) =>
			g.files.every((f) => f.status === 'complete' || f.status === 'error' || f.status === 'processing')
		);
		if (allDone) {
			this.groups = [];
			this.visible = false;
		}
	}

	markProcessingComplete() {
		for (const group of this.groups) {
			for (const file of group.files) {
				if (file.status === 'processing') file.status = 'complete';
			}
		}
		this.groups = [...this.groups];
	}
}

function inferGroupKey(filename: string): string {
	const parts = filename.split(/[/\\]/);
	if (parts.length > 1) return parts[parts.length - 2] ?? 'Upload';
	const base = filename.replace(/\.[^.]+$/, '');
	const match = base.match(/^(\d+)[._\s-]+(.+)$/);
	if (match) return match[2] ?? base;
	return base || 'Upload';
}

export const uploadManager = new UploadManager();
