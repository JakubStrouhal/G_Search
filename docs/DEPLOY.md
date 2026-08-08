---
created: 2026-08-08
updated: 2026-08-08
note: Owner runbook, split out of README.md so the README can address a reviewer only. Content moved unchanged apart from compression; no claim was added or dropped in the move.
---

# Deploy — the owner runbook

**Audience: whoever owns the Vercel and Supabase projects.** Nothing here is needed to read or
review the submission — `README.md` covers that. Status lives in `INDEX.md`.

```
branch → PR to main → GitHub Actions build gate → merge → Vercel builds production
                                                    ↑
                            schema is pushed by hand, before the merge
```

## What is automated

`.github/workflows/ci.yml` runs on every PR to `main` and every push to `main`: `npm ci` at the
root (middleware's one dependency), `npm --prefix web/app ci`, then `npm --prefix web/app run
build` — the same two-part install `vercel.json` runs, so CI cannot pass on a tree Vercel fails to
build. That build is `vue-tsc -b && vite build`, so type errors fail the gate. There is no separate
typecheck job and no test job, because there are no tests. Vercel deploys through its own Git
integration — a preview per PR, production on `main`.

**It builds from the repo root, not from `web/app`.** `prebuild` runs
`web/app/scripts/copy-explainer.mjs`, which reads
`docs/analysis/004-data-story/outputs/explainer.html` from outside the app folder. Setting Vercel's
Root Directory to `web/app` breaks that silently — leave it at the repo root.

`prebuild` runs a second script: `scripts/check-writeup-fixture.mjs` compares a SHA-256 of
`WRITEUP.md`'s body against the `source_sha256` in the fixture the Part C page renders, and **fails
the build** if they differ. Editing Part C's markdown without re-running
`011-writeup/build_writeup.py` is a stale page; the check exists so it cannot ship silently.

## Routing — the explainer *is* the landing page

`copy-explainer.mjs` writes the built page to **both** `public/index.html` and
`public/explainer.html`, so `/` and `/explainer.html` serve the same file. The Vue app is therefore
not the root document: its entry is `web/app/app.html`, named in `vite.config.ts`'s
`rollupOptions.input`, and `vercel.json` rewrites `/app` onto `/app.html`. Both public copies are
gitignored and rebuilt on every dev and build run.

Two consequences worth knowing: a Vercel rewrite of `/` would *not* have worked — rewrites are
evaluated after the filesystem and `index.html` is a real file — and the sign-out button lives in
the Vue app, so it is on `/app`, not on the landing page.

A second rewrite of the same shape, `/api` → `/api.html`, serves the schema viewer. That page reads
the PostgREST spec through `/__spec`, a proxy branch inside `middleware.ts` holding
`SUPABASE_SECRET_KEY` server-side — hosted Supabase closed the OpenAPI root to publishable keys, so
the browser cannot fetch it directly.

## The password gate

`middleware.ts` at the repo root returns **401 and a login form on every path** — the app shell,
the hashed assets and `explainer.html` alike — until a cookie signed with the password is
presented. It runs on Vercel's edge, ahead of the CDN, which is the only place a request for a
cached static file is visible at all; a gate inside the Vue app would leave `explainer.html` served
straight off the CDN beside it.

```bash
npx vercel env add SITE_PASSWORD preview
npx vercel env add SITE_PASSWORD production
```

`SITE_PASSWORD` **must be set per environment** — preview and production are separate scopes. It
carries **no `VITE_` prefix**, deliberately: anything `VITE_`-prefixed is inlined into the browser
bundle. **With the variable unset the deployment serves 503 on every path** and never falls through
to the site — a gate that opens when misconfigured is not a gate. Rotating the password invalidates
every cookie already issued, because the cookie's signing key is derived from it. `npm run dev` is
ungated: Vite does not run Vercel middleware, so the gate is a property of the deployment, not of
the code under it.

**Write the passphrase down before you type it.** The Vercel CLI marks new variables **sensitive by
default on Production and Preview** (`vercel env add --no-sensitive` is the opt-out; its own help
says that flag is what keeps the value readable later). A sensitive variable cannot be read back —
if it is lost, the only route is `vercel env update`, which rotates it and, by design, logs
everyone out.

There is no rate limiting and no audit trail — one shared password, so **use a four-word
passphrase**; entropy is the only brute-force control this design has. Design and limits:
`docs/analysis/009-access-gate/SPEC.md`.

**Not indexed.** `vercel.json` serves `X-Robots-Tag: noindex, nofollow` on every path. This is a
hiring deliverable carrying Groupon's name and a critique of Groupon's search, on a personal
deployment; it should be reachable by whoever it was sent to and absent from search results. There
is deliberately **no `robots.txt` `Disallow`** — that would stop a crawler fetching the page, so it
would never read the header, and the URL can end up indexed anyway.

## What is not automated, and why

Migrations. `CLAUDE.md` requires one reviewed migration generated by `supabase db pull --local`,
and explicit per-run approval before mutating SQL runs against the remote project. An automated
`supabase db push` from CI would defeat both. So the schema goes up by hand, and it goes up
**first** — merging a change that needs a new column before the column exists ships a broken
production front end.

```bash
npx supabase link --project-ref <ref>   # once; ref and DB password go in .env, never committed
npx supabase db push                    # review the diff it prints before confirming
```

## Owner-only, in the dashboards

Not doable from this repo.

| Where | What |
|---|---|
| Vercel | connect `JakubStrouhal/G_Search`; Root Directory = repo root; env `VITE_SUPABASE_URL` + `VITE_SUPABASE_PUBLISHABLE_KEY`, and `SITE_PASSWORD` **on preview and production separately** |
| Supabase | create the remote project; take the ref and the **publishable** key from its API settings |

The browser gets the publishable key only — never the legacy anon key, never the secret key.
Anything `VITE_`-prefixed is compiled into the bundle.

## Still owed

`006-one-page/SPEC.md` §5 requires the agent's refusal fixture to run in CI — "a refusal that stops
firing is a regression". It is not wired up: there is no fixture and no agent yet. It gets a job in
`ci.yml` when build step 4 lands, and until then CI does not cover it.
