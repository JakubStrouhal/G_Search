---
created: 2026-08-07
updated: 2026-08-07
note: Builds the access gate — root middleware.ts, root package.json pinning @vercel/functions, and the two-part install in vercel.json and CI — and records that only the four local criteria could be run, because every deployment criterion needs Vercel credentials the owner holds.
---

# Access gate — result

Built 2026-08-07. Spec: `SPEC.md` in this folder.

## What was built

| Scope row | State | Evidence |
|---|---|---|
| **MUST** Root `middleware.ts`, no `matcher` | **done** | `middleware.ts`, byte-for-byte as SPEC §6. No `config` export, so Vercel invokes it on every route |
| **MUST** Root `package.json` + `package-lock.json`, committed | **done** | `@vercel/functions@^3.8.0`; lockfile 10,544 bytes. Neither is gitignored (`git check-ignore` returns nothing for either) |
| **MUST** `installCommand` installs root **and** `web/app` | **done** | `vercel.json`: `npm ci && npm --prefix web/app ci`. `ci.yml` mirrors it with a two-path npm cache, so CI cannot pass on a tree Vercel fails to build |
| **MUST** Fail closed when `SITE_PASSWORD` is unset | **built, not deployed** | 503 with the variable named — verified locally against unset *and* empty (below). The state that matters is criterion 14 on a real deployment, and that has not run |
| **MUST** Verified on a **preview** deployment before production | **NOT DONE — owner's step** | §9 steps 6–8 need Vercel credentials. Criteria 4–14, 16 and 15 are all unrun |
| **HIGH** Cookie signed with a key derived from the password | **done** | `key = SHA-256(SITE_PASSWORD)`; rotating the variable revokes a live cookie — asserted in the harness |
| **NICE** Supabase Vault behind `resolveSecret()` | **not built, as specified** | `resolveSecret()` exists as the named one-line seam. SPEC §11 stands unchanged |
| **CUT** rate limiting · accounts/SSO · gating `npm run dev` · any `supabase/` or front-end change | **stayed cut** | No file under `supabase/` or `web/app/` was touched. `git status` shows only `middleware.ts`, `package.json`, `package-lock.json`, `vercel.json`, `ci.yml`, `README.md` |

**Build order step 1 settled the design.** `npm install @vercel/functions` resolved, and `next` is
a real export of the installed package (`node -e "import('@vercel/functions')…"` lists it). The
undocumented `return undefined` fallback (SPEC G2) never had to be considered.

**README** carries both additions: § Layout names `middleware.ts` and the root `package.json` with
one line each, and § Deploy gains a **Password-gated** block stating the per-environment variable,
the absent `VITE_` prefix and why, the 503-when-unset posture, and that local dev is ungated.

### Local acceptance criteria — all four ran, all four pass

| # | Check | Result |
|---|---|---|
| 1 | `npm ci` at the repo root | **exit 0**; `package-lock.json` written and committed |
| 2 | `npm --prefix web/app run build` | **exit 0** — `vue-tsc -b` clean, built in 140 ms |
| 3 | `grep -rF -- "$P" web/app/dist` and `grep -r "SITE_PASSWORD" web/app/dist`, after 2 | **no match on either** (exit 1). `dist/` existed and held 5 entries, so this is a real read, not an absent-directory pass |
| 3b | `grep -rl "g_demo_gate" web/app/dist` | **no match** — `middleware.ts` is outside `web/app` and never reaches the client bundle |

**Criterion 3 was run against a placeholder passphrase, not the shipped one.** The password has not
been chosen — §9 step 1 is the owner's. What criterion 3 actually establishes is the structural
fact underneath B6: nothing named `SITE_PASSWORD`, and no gate identifier, is present in the built
bundle, and the secret is only ever read at request time by a file Vite does not compile. **The
owner should re-run criterion 3 verbatim with the real passphrase** once it is picked; it costs one
command.

### Beyond the criteria — the middleware's logic was exercised locally, 45/45

Not in the spec, and it does **not** substitute for criteria 4–16. The spec's own criteria are all
HTTP-against-a-deployment, so nothing in it checks whether the branches behave; that is checkable
without Vercel and was worth checking before asking for a deploy. `middleware.ts` was transpiled
with `web/app`'s `tsc` and the exported handler called directly under Node 22 with real `Request`
objects (scratchpad only — no harness is committed, because there is no test runner in this repo
and adding one is scope nobody approved).

Passing: B5 unset **and** empty → 503 naming the variable · B1 401 on `/`, `/explainer.html`,
`/assets/<hashed>.js`, `/favicon.svg`, `/icons.svg` · B2 the form links no external asset and
inlines its CSS · B3 correct password → 303, `location` = the `next` value, cookie carrying
`Path=/; Max-Age=2592000; HttpOnly; Secure; SameSite=Lax` · B4 wrong password → 401, no
`Set-Cookie`, no echo of the secret · unparseable POST body → 401, never a throw · criterion 13's
open-redirect guard against `https://example.com`, `//example.com` and `javascript:alert(1)`, all
three → `/` · criterion 12 against a flipped signature, five malformed cookies and an expired one,
all → 401 · criterion 10 the cookie opens every path, including when it sits among other cookies ·
**B8 rotating the password 401s a live cookie, and restoring it re-opens** · the hidden `next`
field is HTML-escaped, so a path like `/x"><script>` cannot break out of the attribute.

## What was skipped, and why

- **Criteria 4–14, 16 and 15 — every deployment check.** SPEC §9 assigns steps 6–8 to the owner
  because they need Vercel credentials, and the repo's standing rule is that writes to hosted
  infrastructure belong to the owner. This is not a shortcut taken under time pressure; it is the
  spec's own division of labour, and it means this build **cannot** be reported as working.
- **Criterion 15 is prose beneath the table, not a row.** The table runs 14 → 16. Preserved here.
- **Nothing else.** No scope was added, and nothing the spec asked for turned out to be impossible.

## What is unverified

**The gate is not proven to exist on Vercel.** Everything above is local. The single assumption the
whole design rests on — that Vercel picks up a root `middleware.ts` on a project with an explicit
`buildCommand` and an `outputDirectory` pointing into a subdirectory — is exactly what SPEC §8
names as the thing that would make the spec wrong, and it is unverified. If it is wrong, criteria
4–7 return **200** and the gate silently does not exist.

Unrun, by number: **4** (`/` → 401) · **5** (`/explainer.html` → 401) · **6** (`/assets/index-D0lzT80O.js`
→ 401) · **7** (`/favicon.svg` → 401) · **8** (wrong password → 401, no cookie) · **9** (correct →
303 + cookie attributes) · **10** (cookie re-opens 4–7) · **11** (explainer byte count past the
gate) · **12** (flipped signature → 401) · **13** (open-redirect guard) · **14** (503 on a preview
with the variable never set) · **16** (`x-robots-tag` on the 401 itself) · **15** (4, 5, 6 re-run
against production).

Also unverified, and each is a real risk rather than a formality:

- **Whether `process.env.SITE_PASSWORD` is populated in Vercel's Edge runtime as assumed.** If it
  is not, criterion 14's 503 fires on *every* request even with the variable set. SPEC §8's fix is
  the Node runtime, not deleting the fail-closed branch.
- **Whether adding a root `package.json` changes Vercel's framework detection.** `framework`,
  `buildCommand` and `outputDirectory` are pinned in `vercel.json`, so this is unlikely — but the
  local build passing says nothing about it. Read the preview build log.
- **The CI change.** `ci.yml` was edited, not run. It will first execute on the PR.
- **Cost per request.** Middleware now runs on every asset. Nothing measures it — SPEC's honesty
  register already carries this, and the local harness does not change it.
- **Spec conformance unvalidated — reviewer unavailable.** `.claude/hooks/codex-interview.sh
  implement docs/analysis/009-access-gate/SPEC.md` exited **3**: Codex review is disabled by the
  operator (`.claude/codex-review.disabled` exists), so it did not run. That is an unknown, not a
  pass. **Nothing here has been independently checked against the spec.**

## Where the spec was wrong

**Criterion 11's constant is stale. `explainer.html` is 361,602 bytes, not 354,528.** The build's
`prebuild` step copies `docs/analysis/004-data-story/outputs/explainer.html` into
`web/app/public/`, and that source was regenerated at 16:54 today — three minutes after SPEC.md was
last written at 16:51. Criterion 2 therefore updates `dist/explainer.html` to 361,602 on any run.

**This must not trigger SPEC §8's "Stop; that is worse than having no gate."** That clause is about
the *gate* transforming the deliverable, and the gate does not exist yet — the cause here is an
upstream artifact that was regenerated, which is ordinary. What B7 actually means is *bytes past
the gate == bytes in the locally built `dist`*. So **criterion 11's expected value is whatever
`wc -c < web/app/dist/explainer.html` reports at the time of the deploy**, which is 361,602 as of
this build, and the check should read the local file rather than a constant. A pasted 354,528 would
have failed a working gate.

**`web/app/public/explainer.html` is gitignored**, so this costs no diff noise in the gate commit —
worth stating, because the obvious worry is that a build side effect lands in an unrelated commit.

**One behaviour the spec does not mention.** With a valid cookie, `GET /__gate` calls `next()` and
falls through to whatever the static build serves for an unknown path. Harmless — there is nothing
at `/__gate` to leak, and the POST branch is unaffected — but it is a live path the spec never
describes. Left exactly as §6 wrote it; changing it would be unapproved scope.

**A side effect the spec does not mention, checked rather than assumed.** The root `package.json`
declares `"type": "module"`, and Node resolves a `.js` file's module format from the nearest
`package.json` **up the tree** — so every `.js` outside `web/app` just changed default from CommonJS
to ESM. The one file that could break is `docs/analysis/live_probe.js`. It uses neither `require(`
nor `module.exports` (grepped across every `.js` outside `node_modules`, `web/app` and `.venv` —
no hits), and it is a browser-console paste script rather than something Node runs. **Nothing
broke.** Recorded because the check is invisible in the diff and someone will otherwise have to
redo it.

**B6's mechanism was tested, not assumed, and the result narrows the claim.** SPEC B6 says "Vite
inlines `VITE_`-prefixed vars into the bundle". Measured: the two `VITE_SUPABASE_*` values in
`web/app/.env.local` each appear in exactly **1** file under `dist` — so prefixed *and referenced*
vars really are inlined verbatim. But adding both `SITE_PASSWORD=…` and `VITE_SITE_PASSWORD=…` to
`.env.local` and rebuilding put **neither** in `dist`, because Vite substitutes
`import.meta.env.VITE_X` only where source code reads it, and nothing reads that name.
(`.env.local` was restored from a backup afterwards; SHA-256 identical before and after.) **So the
`VITE_` prefix is not a leak by itself — it is what makes the value available to any client code
that later asks for it, including a bare `import.meta.env`.** The naming rule stands; criterion 3's
grep is what enforces it, and this is why the criterion exists rather than a comment.

**An operational trap the spec does not mention: Vercel stores the variable write-only.**
`vercel env add --help` on CLI 54.14.0 documents `--no-sensitive` as opting out of "the sensitive
default on Production and Preview", where the non-sensitive value "remains readable later". So
`SITE_PASSWORD` cannot be read back off Vercel once set. Losing it means `vercel env update`, which
rotates it — and under G4 that logs out everyone already holding a cookie. Recorded in README
§ Deploy.

**G8 is blocked: the preview cannot be used to verify the gate.** Measured on the PR #2 preview
(`g-demo-kk1fpxbmz-…`) once CI went green: every path — `/`, `/explainer.html`,
`/assets/index-D0lzT80O.js`, `/favicon.svg`, `/icons.svg` — returns **302 to
`vercel.com/sso-api`**, not 401. **Vercel Authentication is on by default for preview
deployments and intercepts ahead of middleware**, so `middleware.ts` never runs and criteria 4–13
and 16 cannot be executed there. The spec's whole verification plan rests on G8 — "preview, then
re-verify production" — and this is the thing that breaks it. **The owner must turn Vercel
Authentication off for Preview** (Project Settings → Deployment Protection) or use a protection
bypass token; otherwise the only place the gate can be verified is production, which is exactly
what G8 was written to avoid. Worth noting the irony: this is `BRIEF.md` option 2, the one rejected
for producing a token in a URL — it is switched on, and it is what stands in the way.

**Production is public right now, and that is the finding the gate exists for, measured rather than
asserted.** `curl https://g-demo-six.vercel.app/explainer.html` → **200**, `x-vercel-cache: HIT`,
`content-length: 354528`. A logged-out request gets the deliverable straight off the CDN. The
`HIT` is the proof that no application-layer check could have stopped it.

That `354528` also confirms the criterion 11 correction from the other direction: production is
still serving the **old** build, which is where the spec's constant came from. The merge rebuilds
it from 004's regenerated output and it becomes **361,602**. So criterion 11 would have failed on
the first gated production deploy, and the cause would have looked like the gate transforming the
deliverable.

**A second gap in criterion 13, in the same category as `GET /__gate`.** `safeNext` rejects
`//example.com` but accepts **`/\example.com`**: browsers normalise `\` to `/` in the path of a
special scheme, so that `Location` resolves off-origin. Criterion 13's three values do not cover it.
Left unedited — §6 is the approved text and the threat model here is a shared hiring link, not a
phishing target — but it is cheaper written down than rediscovered.

**One place the spec was righter than it looks.** SPEC §10's insistence that criterion 3 run *after*
criterion 2 earned itself: `web/app/dist` was already present from an earlier build, so an
out-of-order run would have grepped stale output and still reported "no match".

## Hours

**≈0.6 h** on this unit (implementation only; `BRIEF.md` and `SPEC.md` were earlier units).

| Tool | Did | Got wrong, and what caught it |
|---|---|---|
| Claude Opus 5 (Claude Code) | Wrote `middleware.ts` from SPEC §6, the `vercel.json`/`ci.yml`/README edits, and the local harness | Would have reported criterion 11 as a spec violation on the 354,528 mismatch. Caught by checking the source artifact's mtime against SPEC.md's — the explainer was regenerated after the spec was written |
| Advisor (review model) | Pre-implementation review | Flagged the stale byte count before the build ran, and pushed the unverified list from a footnote to the load-bearing section of this file |
| npm / `tsc` / Node 22 | Resolved `@vercel/functions`, transpiled `middleware.ts`, ran the 45 logic assertions | `tsc` reported `TS2688: Cannot find type definition file for 'node'` — expected, the repo root has no `@types/node`, and it does not affect Vercel, which compiles middleware without typechecking |

**The honest reading of this build: it is complete as code and unproven as a deployment.** Nothing
here should be described as a working gate until criterion 14 runs on a variable-less preview, then
4–13 and 16 on the next one, then 15 on production.

**And one precondition before any of that: commit and push.** Vercel's Git integration builds what
is pushed, and none of these files is committed yet. A preview taken before they land deploys the
*ungated* site, which serves **200** — and 200 on criterion 14 is indistinguishable from the one
failure SPEC §8 warns about, Vercel not picking the middleware up at all. Either commit first, or
`npx vercel deploy` from the working tree, which uploads local files.
