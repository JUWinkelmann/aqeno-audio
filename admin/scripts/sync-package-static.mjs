import { cpSync, existsSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const adminRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const build = resolve(adminRoot, 'build');
const packaged = resolve(adminRoot, '..', 'src', 'aqeno', 'management', 'static');

if (!existsSync(resolve(build, 'index.html'))) {
	throw new Error('Admin build is missing; run this command only after a successful Vite build.');
}
if (!packaged.endsWith('/src/aqeno/management/static')) {
	throw new Error(`Refusing unexpected package-static destination: ${packaged}`);
}

rmSync(packaged, { recursive: true, force: true });
cpSync(build, packaged, { recursive: true });

// SvelteKit leaves indentation on an otherwise empty generated head line.
// Keep committed generated artifacts compatible with the repository's
// whitespace gate without rewriting any JavaScript/CSS bundle.
const packagedIndex = resolve(packaged, 'index.html');
writeFileSync(
	packagedIndex,
	readFileSync(packagedIndex, 'utf8').replace(/[\t ]+$/gm, ''),
	'utf8'
);
