/**
 * Fail the build if the Part C fixture is stale against its markdown source.
 *
 * The failure this exists to prevent: edit docs/analysis/011-writeup/WRITEUP.md, run
 * check_writeup.py (which reads the MARKDOWN and passes), commit, deploy — and /app#writeup
 * serves the previous prose with nothing anywhere saying so. check_writeup.py verifies the
 * numbers against the data; this verifies the shipped page against the numbers.
 *
 * The comparison is a SHA-256 of the markdown body with front matter excluded, recorded in
 * the fixture at generation time. Not mtime: git does not preserve mtimes, so a fresh clone
 * or a CI checkout would make that test meaningless exactly where it matters.
 *
 * Node only, deliberately — Vercel's build runs `npm run build`, and making the deploy
 * depend on a python3 being present on the build image would trade one silent failure for
 * a louder one. Regenerating is the author's job; this only refuses to ship a stale result.
 *
 * Runs as `predev` / `prebuild`, beside copy-explainer.mjs, which does the same job for Part A.
 */
import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const SRC = resolve(here, '../../../docs/analysis/011-writeup/WRITEUP.md')
const FIXTURE = resolve(here, '../../../docs/analysis/011-writeup/outputs/writeup.json')
const REGEN = 'python3 docs/analysis/011-writeup/build_writeup.py'

let raw
try {
  raw = readFileSync(SRC, 'utf8')
} catch {
  console.error(`check-writeup-fixture: cannot read ${SRC}\n  Part C's source is missing.`)
  process.exit(1)
}

let fixture
try {
  fixture = JSON.parse(readFileSync(FIXTURE, 'utf8'))
} catch {
  console.error(`check-writeup-fixture: cannot read ${FIXTURE}\n  Run: ${REGEN}`)
  process.exit(1)
}

// Same split as build_writeup.py: front matter is stamped on every edit and does not
// reach the page, so it must not force a regeneration.
const body = raw.startsWith('---') ? raw.split('\n---\n').slice(1).join('\n---\n') : raw
const actual = createHash('sha256').update(body, 'utf8').digest('hex')

if (fixture.source_sha256 !== actual) {
  console.error(
    'check-writeup-fixture: FAIL — WRITEUP.md has changed since the fixture was generated.\n' +
      `  fixture: ${fixture.source_sha256 ?? '(absent)'}\n` +
      `  source:  ${actual}\n` +
      `  The page would ship the previous prose. Run: ${REGEN}`,
  )
  process.exit(1)
}

console.log(`check-writeup-fixture: ok — ${fixture.body_words} words, fixture current`)
