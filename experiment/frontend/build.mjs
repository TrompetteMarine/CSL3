// Bundles the front end into ../_static/diss_market (app.js, app.css, fonts/) and writes a
// manifest with the hash of every source file, so a stale bundle can be detected by a test.
import { build } from 'esbuild';
import { createHash } from 'node:crypto';
import { mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';

const out = join('..', '_static', 'diss_market');
rmSync(out, { recursive: true, force: true });
mkdirSync(out, { recursive: true });

const result = await build({
  entryPoints: { app: 'src/main.ts' },
  bundle: true,
  minify: true,
  format: 'iife',
  target: ['es2019', 'chrome90', 'firefox90', 'safari14'],
  outdir: out,
  assetNames: 'fonts/[name]',
  loader: { '.woff2': 'file' },
  legalComments: 'none',
  metafile: true,
  logLevel: 'info',
});

function walk(dir) {
  return readdirSync(dir).sort().flatMap((f) => {
    const p = join(dir, f);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
}
const sha = (p) => createHash('sha256').update(readFileSync(p)).digest('hex');
const sources = Object.fromEntries(
  [...walk('src'), 'package.json', 'package-lock.json', 'build.mjs', 'tsconfig.json'].map((p) => [p, sha(p)]),
);
const outputs = Object.fromEntries(
  Object.entries(result.metafile.outputs).map(([p, o]) => [relative(out, p), { bytes: o.bytes, sha256: sha(p) }]),
);
writeFileSync(join(out, 'build-manifest.json'), JSON.stringify({ sources, outputs }, null, 1) + '\n');
