/**
 * Copy the built Part A explainer into public/ so Vite ships it verbatim.
 *
 * The page is generated — notebook.py → outputs/story_data.json →
 * build_explainer.py → outputs/explainer.html — and its whole claim is that no
 * figure is hand-typed. A second copy checked in under public/ would be the same
 * drift channel that produced FINDINGS.md §9 row 12, so public/explainer.html is
 * gitignored and rebuilt from the deliverable on every dev and build run.
 *
 * Runs as `predev` / `prebuild`. Failing here fails the deploy, which is correct:
 * a build that silently omits the Part A deliverable is worse than a red build.
 */
import { copyFileSync, readFileSync, statSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const SRC = resolve(here, '../../../docs/analysis/004-data-story/outputs/explainer.html')
const DEST = resolve(here, '../public/explainer.html')

let html
try {
  html = readFileSync(SRC, 'utf8')
} catch {
  console.error(
    `copy-explainer: ${SRC} is missing.\n` +
      'It is committed, so this normally means the checkout is partial. To regenerate:\n' +
      '  .venv/bin/python docs/analysis/004-data-story/notebook.py\n' +
      '  python3 docs/analysis/004-data-story/build_explainer.py',
  )
  process.exit(1)
}

// Guard against shipping the template by mistake. The template is the page with
// the numbers taken out; served as-is it renders every figure blank and reads as
// a finished deliverable, which is the worst possible failure mode here.
if (html.includes('__STORY_DATA__')) {
  console.error(
    'copy-explainer: that file still carries the __STORY_DATA__ token — it is the ' +
      'template, not the built page. Run build_explainer.py.',
  )
  process.exit(1)
}

copyFileSync(SRC, DEST)
console.log(`copy-explainer: → public/explainer.html (${Math.round(statSync(DEST).size / 1024)} KB)`)
