---
created: 2026-08-07
updated: 2026-08-07
note: Approves the access gate — one predefined password, held in a Vercel environment variable, checked in root middleware that runs before the CDN. Locks the repo changes Vercel's middleware contract requires (a root package.json and a two-part installCommand), and isolates the Supabase Vault variant behind a single function so it stays a swap rather than a rewrite.
---

# Access gate — spec

Approved to build 2026-08-07. Brief: `BRIEF.md` in this folder.

## Thesis

**The Groupon team gets a link and a password, and everything else on that host — the shell, the
hashed bundle, and `explainer.html` — returns 401 without it. The password is never in the browser
bundle, and the repo is aligned with Vercel's middleware contract rather than betting on it.**

## What this builds, and what it deliberately does not

The brief priced four live options. This spec builds **option 4** — middleware plus a Vercel
environment variable.

**Why not option 2 (free Vercel Authentication + a Shareable Link):** it was worth pricing, and T1
would have settled it, but the credential it produces is a **token in a URL** — forwardable, and it
lands in browser history and `Referer` headers. The request was for a password. This ships one.

**Why not option 3 (Supabase Vault):** the only thing Vault buys over an environment variable is
rotation without a redeploy. It costs a `service_role` key sitting in Vercel's environment and an
extension whose availability on `ewknlggenhrlftdukwme` is still unverified (`BRIEF.md` R3, R5). For a
package that is shared once, that is not a trade worth making. **It stays one function away** — §6
`resolveSecret()` is the entire seam, and §11 names what changes.

| | Component | Why |
|---|---|---|
| **MUST** | Root `middleware.ts`, no `matcher` | Vercel's only request-time hook on a static build. Omitting `matcher` means it runs on **every** route, which closes every matcher hole by construction rather than by regex |
| **MUST** | Root `package.json` + `package-lock.json`, committed | Vercel places middleware "at the same level as your `package.json`", and `next()` ships in `@vercel/functions`. Both are currently absent |
| **MUST** | `installCommand` installs root **and** `web/app` | Otherwise the middleware's one dependency is never installed and the build fails at import |
| **MUST** | Fail closed when `SITE_PASSWORD` is unset | A gate that opens when misconfigured is not a gate |
| **MUST** | Verified on a **preview** deployment before production | The middleware contract on a non-framework project is exactly the class of thing that reads fine in docs and behaves differently in practice |
| **HIGH** | Cookie signed with a key derived from the password | Changing the password revokes every session already handed out, with no second secret to manage |
| **NICE** | Supabase Vault behind `resolveSecret()` | Named, specified, not built. §11 |
| **CUT** | Rate limiting / lockout | State is the problem — edge middleware has none, and adding a store for a demo gate is more surface than it removes. **Entropy is the control**: §7 mandates a four-word passphrase |
| **CUT** | Per-person accounts, SSO, audit trail | `BRIEF.md` option 5. One shared password has no audit trail and revocation is all-or-nothing. Stated, not solved |
| **CUT** | Gating local `npm run dev` | Vite does not run Vercel middleware. Local stays open, deliberately — see §9 |
| **CUT** | Any change to `supabase/`, RLS, grants, or the front end | The gate sits in front of all of it and changes none of it |

## Required behaviour

| # | Behaviour | Traces to |
|---|---|---|
| B1 | Every path returns **401** without a valid cookie — `/`, `/explainer.html`, `/assets/*`, `/favicon.svg`, `/icons.svg` | `BRIEF.md`: the deliverable is a static file, and `x-vercel-cache: HIT` proves the CDN serves it. Middleware runs before the cache |
| B2 | The 401 body is a **self-contained** login form — inline CSS, no external asset | Anything it linked to would itself be gated, so the page would render unstyled |
| B3 | Correct password → `303` + `Set-Cookie`, then a redirect back to the originally requested path | The link a grader is given may point straight at `/explainer.html` |
| B4 | Wrong password → **401** and the form again, with an error. No hint about the correct value | — |
| B5 | `SITE_PASSWORD` unset or empty → **503, deny**. Never fall through to the site | Same posture as `007-embeddings/SPEC.md`: stop and say why |
| B6 | The password never appears in `web/app/dist` | Vite inlines `VITE_`-prefixed vars into the bundle. This one must not carry that prefix, and §10 checks it rather than trusting it |
| B7 | Past the gate, `/explainer.html` is **byte-identical** to what is served today — 354,528 bytes | The gate must not become a wrapper around the deliverable |
| B8 | Changing `SITE_PASSWORD` invalidates every existing cookie | The cookie's signing key is derived from the password |

## What it does when it has no good answer

Three cases, one rule.

1. **`SITE_PASSWORD` is unset** — the deployment is misconfigured. **503, deny, and say which
   variable is missing.** The failure a reviewer will not notice is the opposite one: a gate that
   silently serves the site when its secret is absent looks identical to a working deployment.
2. **The cookie is present but does not verify** — tampered, expired, or signed under a previous
   password. **Treat exactly as absent**: show the form. Do not distinguish the cases in the
   response, because the distinction is only useful to someone probing.
3. **The form posts something unparseable** — no body, wrong content type, missing field. **401 and
   the form.** Never throw: an unhandled exception in middleware is a 500, and a 500 on every path
   is indistinguishable from the site being broken.

## Architecture

**Enforcement point.** Vercel Routing Middleware, `middleware.ts` at the repo root. The Vercel
project's root directory is `.` (`.vercel/repo.json`, `directory: "."`), so repo root **is** project
root. Works with any framework; default runtime is Edge; **runs globally before the cache**.

**No `matcher`.** Vercel invokes middleware for every route when no matcher is set. A matcher would
have to enumerate what *not* to gate, and every entry on that list is a hole — `/assets/*`,
`/_vercel/*`, the favicon. The cost is an invocation per asset request. For a demo that is expected
to be irrelevant, and **nothing here measures it** — if the explainer feels slow past the gate, §10
criterion 11's `curl` is where a `%{time_total}` would go.

**`next()`, not a bare `return`.** `@vercel/functions` exports the helper that continues the chain.
The alternative — returning `undefined` and hoping it falls through — is undocumented for
non-Next projects, and its failure mode is the bad one: **a blank site for authorized visitors**.
Installing one dependency removes the unknown. This is the whole reason the root `package.json`
exists.

**Crypto.** Web Crypto, available in the Edge runtime. No dependency.

- **Password check:** compare base64url SHA-256 digests, not the raw strings. A plain `===` on
  strings short-circuits at the first differing byte.
- **Cookie:** `<expiryMs>.<sig>`, where `sig = HMAC-SHA256(key, "v1.<expiryMs>")` and
  **`key = SHA-256(SITE_PASSWORD)`**. Deriving the key from the password is what makes B8 true and
  removes the second secret that would otherwise need managing.
- **Cookie attributes:** `Path=/; Max-Age=2592000; HttpOnly; Secure; SameSite=Lax`. `HttpOnly` keeps
  it away from any script on the page; `Lax` still sends it on the top-level navigation a pasted link
  produces.

**`resolveSecret()`** is a one-line function returning `process.env.SITE_PASSWORD`. It is a named
function rather than an inline read solely so §11's Vault variant is a body swap.

**Open-redirect guard.** The form carries the originally requested path in a hidden field, and that
value reaches a `Location` header. It is validated: must start with a single `/`, must not start with
`//`, otherwise it falls back to `/`. Without this the login page forwards anywhere on the internet.

### The files

**`middleware.ts`** (repo root) — full content, to be created as written:

```ts
/**
 * Access gate for the deployed case study.
 *
 * The deliverable is a static file set on Vercel's CDN — `public/explainer.html` is
 * served directly, so a gate inside the Vue app would guard a door next to an open
 * window. Middleware runs before the cache, on every route, which is the only place a
 * request for a hashed asset is visible at all.
 *
 * No `config` export: with no `matcher`, Vercel invokes this for every route. That is
 * deliberate — a matcher is a list of what NOT to gate, and every entry is a hole.
 */
import { next } from '@vercel/functions'

const COOKIE = 'g_demo_gate'
const GATE_PATH = '/__gate'
const TTL_SECONDS = 30 * 24 * 60 * 60

const enc = new TextEncoder()

/** The single seam the Supabase Vault variant would replace. See SPEC §11. */
function resolveSecret(): string | undefined {
  return process.env.SITE_PASSWORD
}

function b64url(buf: ArrayBuffer): string {
  let s = ''
  for (const byte of new Uint8Array(buf)) s += String.fromCharCode(byte)
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

async function digest(value: string): Promise<string> {
  return b64url(await crypto.subtle.digest('SHA-256', enc.encode(value)))
}

/** Fixed-length inputs only. Lengths differ => already not equal, and no secret leaks. */
function equalConstantTime(a: string, b: string): boolean {
  if (a.length !== b.length) return false
  let diff = 0
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i)
  return diff === 0
}

/**
 * The signing key IS the password's digest. Rotating SITE_PASSWORD therefore
 * invalidates every cookie already issued — no second secret, no revocation list.
 */
async function sign(message: string, secret: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    'raw',
    await crypto.subtle.digest('SHA-256', enc.encode(secret)),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  )
  return b64url(await crypto.subtle.sign('HMAC', key, enc.encode(message)))
}

function readCookie(header: string | null, name: string): string | undefined {
  if (!header) return undefined
  for (const part of header.split(';')) {
    const eq = part.indexOf('=')
    if (eq < 0) continue
    if (part.slice(0, eq).trim() === name) return part.slice(eq + 1).trim()
  }
  return undefined
}

async function cookieIsValid(raw: string | undefined, secret: string): Promise<boolean> {
  if (!raw) return false
  const dot = raw.indexOf('.')
  if (dot < 1) return false
  const expiry = raw.slice(0, dot)
  const signature = raw.slice(dot + 1)
  const expiryMs = Number(expiry)
  if (!Number.isFinite(expiryMs) || expiryMs <= Date.now()) return false
  return equalConstantTime(signature, await sign(`v1.${expiry}`, secret))
}

/** Same-origin absolute paths only. Without this the form is an open redirect. */
function safeNext(candidate: string): string {
  if (!candidate.startsWith('/') || candidate.startsWith('//')) return '/'
  return candidate
}

const NO_STORE = {
  'content-type': 'text/html; charset=utf-8',
  'cache-control': 'no-store',
  // Set here rather than inherited: vercel.json's headers block applies to served
  // files, and whether it reaches a response middleware authors itself is unverified.
  'x-robots-tag': 'noindex, nofollow',
}

function page(target: string, status: number, error: boolean): Response {
  const to = target.replace(/[&<>"]/g, (c) => `&#${c.charCodeAt(0)};`)
  return new Response(
    `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>Password required</title>
<style>
:root{color-scheme:light dark}
body{margin:0;min-height:100vh;display:grid;place-items:center;
 font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
 background:Canvas;color:CanvasText}
form{width:min(22rem,90vw);display:grid;gap:.75rem}
h1{font-size:1.125rem;font-weight:800;margin:0}
p{margin:0;opacity:.7;font-size:.875rem}
input,button{font:inherit;padding:.625rem .75rem;border-radius:.5rem;
 border:1px solid color-mix(in srgb,CanvasText 25%,transparent)}
input{background:Canvas;color:CanvasText}
button{border:0;background:CanvasText;color:Canvas;font-weight:700;cursor:pointer}
.err{color:#c02626;font-size:.875rem}
</style></head><body><form method="post" action="${GATE_PATH}">
<h1>Groupon case study &middot; R29944</h1>
<p>This deployment is shared privately. Enter the password you were given.</p>
<input type="hidden" name="next" value="${to}">
<input type="password" name="password" autocomplete="current-password"
 autofocus required aria-label="Password">
${error ? '<p class="err">That password is not correct.</p>' : ''}
<button type="submit">Enter</button>
</form></body></html>`,
    { status, headers: NO_STORE },
  )
}

export default async function middleware(request: Request): Promise<Response> {
  const secret = resolveSecret()

  // Fail closed. Serving the site because the secret is missing is the failure nobody
  // notices — it looks exactly like a working deployment.
  if (!secret) {
    return new Response(
      'This deployment is not configured: SITE_PASSWORD is unset.',
      { status: 503, headers: { 'content-type': 'text/plain', 'cache-control': 'no-store' } },
    )
  }

  const url = new URL(request.url)

  if (await cookieIsValid(readCookie(request.headers.get('cookie'), COOKIE), secret)) {
    return next()
  }

  if (request.method === 'POST' && url.pathname === GATE_PATH) {
    let candidate = ''
    let target = '/'
    try {
      const form = await request.formData()
      candidate = String(form.get('password') ?? '')
      target = safeNext(String(form.get('next') ?? '/'))
    } catch {
      // Unparseable body — treated as a wrong password, never as a 500.
    }

    if (equalConstantTime(await digest(candidate), await digest(secret))) {
      const expiry = Date.now() + TTL_SECONDS * 1000
      const value = `${expiry}.${await sign(`v1.${expiry}`, secret)}`
      return new Response(null, {
        status: 303,
        headers: {
          location: target,
          'cache-control': 'no-store',
          'set-cookie':
            `${COOKIE}=${value}; Path=/; Max-Age=${TTL_SECONDS}; HttpOnly; Secure; SameSite=Lax`,
        },
      })
    }
    return page(target, 401, true)
  }

  return page(url.pathname + url.search, 401, false)
}
```

**`package.json`** (repo root) — new. **Do not hand-write the dependency version**; §9 step 2 runs
`npm install` and lets npm pin it.

```json
{
  "name": "g-demo",
  "private": true,
  "type": "module",
  "description": "Repo root. Exists so Vercel resolves middleware.ts and its one dependency; the application lives in web/app.",
  "dependencies": {}
}
```

**`vercel.json`** — one line changes. Everything else, including the existing `headers` block, stays:

```diff
-  "installCommand": "npm --prefix web/app ci",
+  "installCommand": "npm ci && npm --prefix web/app ci",
```

**`.github/workflows/ci.yml`** — the build gate must exercise the same install, or CI passes on a
tree Vercel cannot build:

```diff
           cache: npm
-          cache-dependency-path: web/app/package-lock.json
+          cache-dependency-path: |
+            package-lock.json
+            web/app/package-lock.json
 
-      # `npm ci` hard-fails if package-lock.json is out of sync with package.json.
+      # `npm ci` hard-fails if either package-lock.json is out of sync. The root one
+      # carries middleware.ts's dependency; Vercel installs both the same way.
+      - run: npm ci
       - run: npm --prefix web/app ci
```

**`.gitignore`** — no change needed. `node_modules/` and `dist/` already match at any depth; the new
root `package-lock.json` is not matched by anything and will be committed.

## What the person running this has to do

Steps 1–5 are the agent's. **Steps 6–8 are the owner's** — they need Vercel credentials, and the
repo's standing rule is that writes to hosted infrastructure belong to the owner.

```bash
# 1. Pick the password. Four words, ~50 bits. Entropy is the only brute-force control
#    this design has (rate limiting is CUT, §2), so a short one is a real weakness.

# 2. Root dependency. Creates package-lock.json; commit both files.
npm install @vercel/functions

# 3. The build still has to pass unchanged.
npm --prefix web/app ci && npm --prefix web/app run build

# 4-5. middleware.ts, vercel.json, ci.yml, README — per §6.

# 6. OWNER: preview deploy FIRST, with no variable set anywhere. This is criterion 14 —
#    the fail-closed branch, in the state it actually occurs in: a forgotten variable.
npx vercel deploy

# 7. OWNER: set it. NOT VITE_-prefixed, or Vite inlines it into the bundle. Then redeploy.
npx vercel env add SITE_PASSWORD preview
npx vercel env add SITE_PASSWORD production
npx vercel deploy          # criteria 4-13 and 16 run against THIS url, never production

# 8. OWNER: only after §10 passes end to end. Then criterion 15 on production.
npx vercel deploy --prod
```

## Acceptance criteria

Each is true or false, and each is a command. `$U` is the preview URL, `$P` the password.

**Run order matters, and it saves two deploys.** **1–3 are local**, after step 3's build. **14 runs
on the *first* preview deploy, before `SITE_PASSWORD` has ever been set** — that is the fail-closed
branch in the exact state it occurs in real life, a fresh environment where the variable was
forgotten. Only then does the owner add the variable and redeploy; **4–13 and 16 run against that
second preview**, and **15 against production**. Verifying 14 by *removing* a variable that is
already set would cost two extra owner round-trips and leave the preview serving 503 in between.

| # | Check | Pass |
|---|---|---|
| 1 | `npm ci` at the repo root | exits 0; `package-lock.json` exists and is committed |
| 2 | `npm --prefix web/app run build` | exits 0 — `vue-tsc -b` still passes, nothing in `web/app` regressed |
| 3 | **After criterion 2, never before** — `grep -rF -- "$P" web/app/dist` and `grep -r "SITE_PASSWORD" web/app/dist` | **no match on either.** B6, the one check that proves the password is not shipped to browsers. `-F` because a passphrase containing `.` or `\|` is otherwise read as a regex. `dist/` is gitignored and only exists after the build — running this against an absent directory also reports "no match", which is why the ordering is stated rather than assumed |
| 3b | `grep -rl "g_demo_gate" web/app/dist` | **no match** — `middleware.ts` lives outside `web/app` and must not reach the client bundle. Cheap, and it is the assumption criterion 3 rests on |
| 4 | `curl -so /dev/null -w '%{http_code}' $U/` | **401** |
| 5 | `curl -so /dev/null -w '%{http_code}' $U/explainer.html` | **401** — the deliverable, and the reason a front-end gate fails |
| 6 | `curl -so /dev/null -w '%{http_code}' $U/assets/<hashed>.js` | **401.** Read the real filename out of the built `index.html` first; a gate that misses the bundle renders a blank page |
| 7 | `curl -so /dev/null -w '%{http_code}' $U/favicon.svg` | **401** — confirms "no matcher" gates non-HTML too |
| 8 | POST a wrong password to `$U/__gate` | **401**, body contains the error text, **no** `set-cookie` |
| 9 | POST the correct password | **303**; `location` is the `next` value; `set-cookie` carries `HttpOnly`, `Secure`, `SameSite=Lax` |
| 10 | Re-request 4–7 with that cookie | all **200** |
| 11 | `curl -s -b <cookie> $U/explainer.html \| wc -c` | **354528** — B7, byte-identical to what is served today |
| 12 | Flip one character in the cookie signature and re-request | **401** |
| 13 | POST `next=https://example.com`, then read `location` | **`/`**, not the external URL. The open-redirect guard |
| 14 | **First preview deploy, `SITE_PASSWORD` never set** — `curl -s -w '%{http_code}' $U/` | **503**, body names the missing variable, and the site is **not** served. B5 |
| 16 | `curl -sI $U/` unauthenticated | `x-robots-tag: noindex, nofollow` **on the 401 itself**. The middleware sets this on its own responses rather than inheriting it, because whether `vercel.json`'s `headers` block reaches a middleware-authored response is unverified (`BRIEF.md` R2) — so it needs a check, not a comment |

**Criterion 15, and it is the one that decides whether this shipped: after promoting to production,
re-run 4, 5 and 6 against `https://g-demo-six.vercel.app`.** Preview and production are separate
environment scopes; a variable set on one is not set on the other. This repo has already been caught
once by assuming a verified environment transfers (`INDEX.md` 4.1, local vs remote grants). Do not
assume it twice.

## Honesty register

Carries into Part C.

- **This is a shared password with no audit trail.** Everyone who has it is the same visitor, and
  revoking it revokes everyone. That is the correct shape for a hiring panel and the wrong shape for
  anything else.
- **There is no rate limiting.** The password can be guessed at HTTP speed. A four-word passphrase
  makes that infeasible; a short one does not, and the design has no second line of defence.
- **The threat model is proportionate and should be stated as such.** This keeps the work out of
  search results and stops the link being casually forwarded. The repo holds no personal data — the
  CSVs are synthetic and supplied by Groupon. It is not built to resist a determined attacker.
- **The password lives in Vercel, not Supabase, and that was the request.** §11 is the upgrade path
  and it is honestly small; what it buys is rotation without a redeploy, and nothing else.
- **Local development is ungated.** Vite does not run Vercel middleware, so `npm run dev` serves
  everything. Deliberate — the gate is a property of the deployment, not of the code under it.
- **Middleware now runs on every request, including each hashed asset, and no criterion measures
  what that costs.** Stated because it is the gap: the design assumes the overhead is irrelevant at
  this size rather than showing it. If it ever matters, the fallback is to gate HTML only — which is
  **weaker**, and would have to be recorded as a weakening rather than adopted quietly.

## What would make this spec wrong

- **Vercel does not pick up `middleware.ts` with an explicit `buildCommand` and an
  `outputDirectory` pointing into a subdirectory** → criteria 4–7 return 200 on the preview. The
  gate does not exist, and no amount of local checking would have shown it. This is why every
  criterion runs against a deployment.
- **Adding a root `package.json` changes Vercel's framework detection** and breaks the build →
  criterion 2 passes locally while the preview build fails. Read the build log, not the local exit
  code. `framework`, `buildCommand` and `outputDirectory` are all pinned in `vercel.json`, so this
  is unlikely rather than impossible.
- **`process.env` is not populated in the Edge runtime the way this assumes** → criterion 14's 503
  fires on every request even with the variable set. The fix is the Node.js runtime
  (`export const config = { runtime: 'nodejs' }`), not removing the fail-closed branch.
- **`explainer.html` is not 354,528 bytes past the gate** → something is transforming the
  deliverable. Stop; that is worse than having no gate.

## Build order

Whatever can invalidate the plan goes first.

1. **Root `package.json` + `npm install @vercel/functions`.** If the dependency does not resolve,
   the `next()` design is wrong and the undocumented `return undefined` fallback becomes the only
   route — settle that before writing anything else.
2. **`middleware.ts`** exactly as §6.
3. **`vercel.json` `installCommand`** and **`ci.yml`**. Both, in the same commit as (1) — a root
   `package.json` that Vercel never installs fails the build at import, and CI that does not install
   it passes on a tree that cannot deploy.
4. **`npm --prefix web/app run build`** locally. Criteria 1, 2, then 3 and 3b — in that order, since
   3 reads the directory 2 produces.
5. **README § Layout**: add `middleware.ts` and the root `package.json` with one line each on why
   they exist. **README § Deploy**: state that the deployment is password-gated and that
   `SITE_PASSWORD` must be set per environment.
6. **Hand to the owner** for §9 step 6 — a preview deploy with **no variable set** — and run
   **criterion 14** against it. Then step 7 sets the variable and redeploys, and criteria **4–13 and
   16** run against that second preview.
7. **Promote**, then run criterion 15. Nothing is done until 15 passes.
8. **`RESULT.md`**: the criteria table with actual values, and whatever was found that this spec did
   not predict.

## Decision log

| # | Question the brief left open | Resolution | Why |
|---|---|---|---|
| **G1** | Which of the four options ships? | **Option 4** — middleware + Vercel env var | A password was asked for, so option 2's URL token is out; Vault's only gain is redeploy-free rotation, at the price of a `service_role` key in Vercel and an unverified extension |
| **G2** | Continue the chain with `next()` or a bare `return`? | **`next()`**, and accept the root `package.json` | The bare return is undocumented for non-Next projects and fails blank rather than loudly. One dependency converts an unknown into a fact |
| **G3** | `matcher`, or none? | **None** | A matcher enumerates what is *not* gated. Every entry is a hole, and the holes are exactly the paths that carry the deliverable |
| **G4** | Where does the cookie's signing key come from? | **Derived from the password** | Rotation revokes every live session for free, and there is no second secret to store, leak or forget |
| **G5** | Missing `SITE_PASSWORD` — deny or serve? | **Deny, 503** | Serving is the failure nobody notices; it is indistinguishable from a healthy deployment |
| **G6** | Rate limiting? | **No — entropy instead**, and it is named as a limitation | Edge middleware has no state. Adding a store for a demo gate adds more surface than it removes |
| **G7** | Does the login page carry Groupon branding? | **No** | `docs/design/DESIGN-SYSTEM.md` §9's rule against inventing an asset in their name applies hardest to the first page they see |
| **G8** | Verify on production or preview? | **Preview, then re-verify production** | Environment variables are scoped per environment, and this repo has already been caught assuming a verified environment transfers |

## §11 — the Supabase Vault variant, if it is ever wanted

Not built. Recorded so it stays a swap.

`resolveSecret()` becomes an `async` fetch of a `security definer` RPC that reads
`vault.decrypted_secrets` and returns a **boolean**, never the plaintext — which means the
password-comparison branch moves into Postgres and the cookie's signing key can no longer be derived
from the password. It would need its own Vault-held secret, and G4's free revocation becomes a second
thing to manage. **Be concrete about the cost of that:** it is **two Vault-backed calls, not one** —
an RPC to check the password on submit, plus a read of a separate signing secret on any cold cookie
verification — so both need caching in the isolate, and both need a fail-closed path. **The
middleware would also need one extra env var (`SUPABASE_URL`) and the key from `BRIEF.md` Q3** —
recommended there as the `service_role` key, granted to nothing else.

What it buys: `select vault.update_secret(...)` rotates the password with no redeploy.
What it costs: a full-privilege database key in Vercel's environment, two cached round trips and two
fail-closed paths, and `BRIEF.md` R5 still unverified.

**Do not build it because it is the more interesting design.** Build it if redeploy-free rotation is
actually needed.
