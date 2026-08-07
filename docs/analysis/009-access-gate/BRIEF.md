---
created: 2026-08-07
updated: 2026-08-07
note: Opens the access-gate unit — establishes that a database-level gate protects nothing here (the deliverable is a static file on a CDN), then puts one free five-minute test in front of the build, because it can gate the site at zero cost and make the Supabase-Vault design unnecessary.
---

# Access gate — what actually locks the live site, and what each option costs

Opened 2026-08-07. **Plan only — nothing below has been executed.**

## The recommendation, before the reasoning

**Run T1 first — one toggle and two `curl`s, fully reversible.** If it passes, the site is gated
today for free with no code, and the right move is to stop and put the hours into Part C, which
`INDEX.md` names as the larger of the two remaining risks. If it fails, build option 3: middleware at
the edge with the passphrase in Supabase Vault.

**And the trade in that, stated rather than resolved here, because it is yours to make.** You asked
for the password to live in **Supabase Vault**. The free path does not do that. What you give up:
the credential becomes a **URL token** rather than a typed passphrase — forwardable, and it lands in
browser history and `Referer` headers — and nothing about it lives in Supabase. What you get back:
zero code, zero cost, revocable from a dropdown, and a day not spent on a login form. **If the
passphrase-in-Supabase property matters to you for its own sake, say so and option 3 is the plan** —
it is fully designed below either way.

## The question

`https://g-demo-six.vercel.app` is live and **completely public**. Verified by probe, not assumed
(2026-08-07):

| path | status | note |
|---|---|---|
| `/` | 200 | the Vue shell, `SiteIndex.vue` |
| `/explainer.html` | 200 | **354,528 bytes — the entire Part A deliverable** |
| `/assets/index-*.js` | 200 | `x-vercel-cache: HIT`, so it is served from the CDN edge |

The only access control today is `X-Robots-Tag: noindex, nofollow` from `vercel.json`. That is a
request to search engines, not a lock. Anyone with the URL has everything.

**The ask: one shared passphrase, stored in Supabase, that can be given to the Groupon team.**

## The fact that decides the design

**The deployed artifact is a static Vite build. The payload is a file, not a query result.**

`web/app/scripts/copy-explainer.mjs` copies `004-data-story/outputs/explainer.html` into `public/`
at build time; Vite ships it verbatim; Vercel serves it from the CDN. The front end's only Supabase
call today is `HealthCheck.vue`, and `web/app/.env.local` still points at `localhost`.

So: **RLS, Supabase Auth and grant changes protect nothing here.** They gate rows, and there are no
rows on the wire. A logged-out visitor who types `/explainer.html` gets the bytes regardless of what
the database says. This kills the most obvious reading of the request — "use Supabase Auth" — before
any of it gets built.

That splits the ask into two decisions that must be made separately, because bundling them is what
makes this kind of proposal impossible to evaluate:

| | Decision | Answer |
|---|---|---|
| **D1** | **Where is the gate enforced?** | **The edge, before the CDN.** Forced by the above — nothing else sees a request for a static asset. Vercel's own protection and a middleware of our own both satisfy this; a database does not |
| **D2** | **Where does the credential live?** | **Open, and it is the only genuinely open question.** Supabase Vault is the ask; a Vercel-issued share token is free. T1 prices the difference |

## What would change the answer

Checked before writing, per the `/brief` rule.

| Fact | Status |
|---|---|
| Does Vercel have built-in password protection? | **Yes, and it is rejected on cost.** Password Protection is **Enterprise, or a $150/month add-on on Pro with a 30-day minimum commitment**. Not proportionate to a case study |
| Is the free tier of it usable? | **Possibly — and this nearly got dismissed too fast, so it is written out.** Vercel Authentication is free on all plans. It normally requires each viewer to hold a Vercel account with project access, which a hiring panel will not — **but a Shareable Link bypasses exactly that**, granting external users access through a query-string token with no account. Hobby can create **one** such link per account, which is one more than this needs. **The catch is scope:** the free tier is *Standard Protection*, and Vercel's own note says it leaves **production domains public**. Whether `g-demo-six.vercel.app` counts as a *production domain* or as a *generated deployment URL* — which Standard Protection does restrict — **is not answerable from the documentation**. It is answerable in five minutes with a toggle and a `curl` (T1 below) |
| Can middleware run on a non-framework Vite project? | **Yes.** Vercel Routing Middleware works with **any framework**: a `middleware.ts` at the project root, default export, `(request: Request)`. It **runs globally before the cache**, which is exactly the property a CDN-cached static file needs |
| Does this project have any request-time hook today? | **No.** No `api/`, no `middleware.ts`, no serverless function. `vercel.json` is a pure static build (`outputDirectory: web/app/dist`). Middleware would be the first |
| Is there a root `package.json`? | **No** — only `web/app/package.json`, installed via `installCommand: npm --prefix web/app ci`. **This is the one real implementation risk**, R1 below |
| Does Supabase have somewhere to put the secret? | **Yes — Vault.** `vault.create_secret(...)`, `vault.update_secret(...)`, read through the `vault.decrypted_secrets` view. Supabase's own docs warn that anyone with access to that view has the plaintext, so the grant matters |
| Does the remote database lag? | **Yes** — migration 3 unapplied, old seed, no vectors (`INDEX.md` Now/Next). **Irrelevant here:** this unit needs one function and one secret, not the seed. Stated so nobody blocks on it |
| Is `supabase_vault` enabled on `ewknlggenhrlftdukwme`? | **Unverified.** R5 below — settle before the SPEC |

**Two things could still make this unit unnecessary, and both are cheap to check.** If the Vercel
account already carries Pro + Advanced Deployment Protection, option 1 is a settings toggle. And if
**T1** (below) comes back protected, option 2 is a settings toggle *on the free plan*. **Run T1
before building anything.**

## The options

| # | Option | Enforced | Secret lives | Verdict |
|---|---|---|---|---|
| 1 | Vercel **Password Protection** | Vercel edge | Vercel | **Rejected — $150/mo, 30-day minimum**, and the secret is not in Supabase |
| 2 | Vercel **Authentication** + one **Shareable Link** | Vercel edge | a URL token | **Run T1 before choosing anything else.** Free, zero code, revocable from a dropdown, and the recipient needs no Vercel account. **Conditional on T1**, and it does not put the secret in Supabase — see below |
| 3 | **Routing Middleware + passphrase in Supabase Vault** | Edge, before cache | **Supabase Vault** | **The plan if T1 fails** — and the plan regardless if the passphrase-in-Supabase property is wanted for its own sake. Fully designed below |
| 4 | Routing Middleware + passphrase in a Vercel env var | Edge, before cache | Vercel env | **Fallback.** Simplest thing that works; loses rotation-without-redeploy, and does not meet the ask |
| 5 | Supabase **Auth** account(s), middleware validates the JWT | Edge, before cache | `auth.users` (hashed) | **Named, not now.** It is option 3 *plus* cookie-session handling in a static SPA. Build it only if per-person revocation and an audit trail are wanted |
| 6 | Client-side route guard in the Vue app | Nowhere | — | **Not an option — it does not gate.** `/explainer.html` and `/assets/*` stay directly fetchable by URL, as the probe above shows. Listing this as a ranked choice in a package graded on honesty about limits would be worse than not proposing a gate at all |

**T1 — the test that has to run first, because it can make options 3–5 unnecessary.** Toggle Vercel
Authentication on at *Standard Protection*, create the one Shareable Link, then run **four** probes
from a client with **no Vercel cookie**. Four, not one, because "is it gated" and "does the share
token actually work" are different questions and a gate that passes the first and fails the second
renders a **blank page** — the same worst-case failure mode as R1.

| # | probe | pass |
|---|---|---|
| a | `GET /explainer.html`, no token | **not 200** (401 or a redirect to Vercel login) |
| b | `GET /assets/index-*.js`, no token | **not 200** — if the HTML is gated but the bundle is not, the gate is decorative |
| c | `GET /explainer.html` **with** the share token | **200**, and the bytes match the ungated size, 354,528 |
| d | `GET /assets/index-*.js` **with** the share token | **200** — otherwise the shell loads and renders nothing |

**All four pass → option 2 is live and everything below is optional. Any one fails → option 2 is
dead and option 3 is the plan.** Cost: one toggle, four commands, fully reversible.

**Why option 3 is still worth writing even if T1 passes.** Two honest reasons and one non-reason:

- **The link *is* the credential.** A Shareable Link is a token in a query string — it lands in
  browser history, in `Referer` headers, and in whatever chat window forwards it. That is *weaker*
  than a passphrase typed into a form, not stronger, and the convenience is what makes it weaker.
- **It is not the ask.** The request was for a password held in Supabase. Option 2 holds nothing in
  Supabase.
- **Not a reason:** that option 3 is more interesting to build. If T1 passes and the shortcomings
  above are acceptable, **take option 2 and spend the hours on Part C**, which `INDEX.md` names as
  the larger risk of the two.

**Why 3 over 4** — the honest answer is *one* property, and it should be stated as one rather than
dressed up: **the passphrase can be rotated by running one SQL statement, with no redeploy and no
Vercel dashboard access**, and because the session cookie is signed with a key derived *from* the
passphrase, rotating it also invalidates every session already handed out. Option 4 needs a redeploy
to change the password and has no revocation story at all. If that property is not wanted, take
option 4 — it is ~40 lines and no database work.

## How option 3 works

**Request path.** `middleware.ts` at the repo root, matching every path except its own POST endpoint.

1. **Cookie present and valid** → return `next()`, the request proceeds to the static file.
2. **No cookie** → the middleware returns a **self-contained HTML login form** (inline CSS, no
   external assets, so there is nothing to whitelist in the matcher).
3. **`POST /__gate`** → the middleware calls a Supabase RPC with the submitted passphrase. On `true`
   it sets the cookie and redirects; on `false` it re-renders the form with an error.

**Cookie.** `HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=30d`, value `exp.HMAC-SHA256(exp, k)`.
**`k` = SHA-256 of the passphrase read from Vault**, cached in the isolate for ~5 minutes. That is
what makes rotation revoke: change the secret, every outstanding cookie stops verifying. No separate
signing secret to manage.

**Vault read fails** — network, missing secret, changed grant — **deny and say why.** Fail closed,
never open. Same posture `007-embeddings/SPEC.md` already establishes for a missing model: stop and
state the reason, do not substitute.

**The database side**, sketched — the SPEC owns the final text:

```sql
-- The secret. Created once; rotated in place, which revokes every live session.
select vault.create_secret('<passphrase>', 'demo_gate_passphrase',
                           'Shared passphrase for the deployed case-study site');

create or replace function public.check_access_passphrase(candidate text)
returns boolean language plpgsql security definer set search_path = '' as $$
declare stored text;
begin
  select decrypted_secret into stored
    from vault.decrypted_secrets where name = 'demo_gate_passphrase';

  if stored is null or candidate is null then
    return false;                          -- fail closed: no secret, no entry
  end if;

  -- Compare fixed-length digests, not the raw strings. A plain `=` on text
  -- short-circuits at the first differing byte and leaks the prefix by timing.
  return encode(extensions.digest(stored,    'sha256'), 'hex')
       = encode(extensions.digest(candidate, 'sha256'), 'hex');
end $$;

revoke all on function public.check_access_passphrase(text)
  from public, anon, authenticated;
grant execute on function public.check_access_passphrase(text) to service_role;
```

The function returns a boolean and never the secret, so the plaintext stays inside Postgres. The
`revoke`-then-`grant` shape is deliberate and is the same lesson `INDEX.md` 4.1 already paid for:
**state the end state absolutely, because local and remote default ACLs differ.**

## The matcher, and what stays reachable without the passphrase

Writing this out because it is where the design is most likely to be quietly wrong.

```ts
export const config = { matcher: ['/((?!__gate).*)'] }
```

That covers `/`, `/explainer.html`, `/assets/*`, `/favicon.svg`, `/icons.svg` — **everything the
build emits**. Middleware runs before the cache, so the `x-vercel-cache: HIT` on the JS bundle does
not bypass it.

**Reachable without the passphrase, after this ships:**

1. **The login page itself** — unavoidable, it is the form.
2. **`POST /__gate`** — unavoidable, it is the check.
3. **The existence of the site** and its TLS certificate. Not the `<title>` or the `og:` metadata:
   those live in `index.html`, which is gated.
4. **`/_vercel/*`** — Vercel's own instrumentation endpoints. **Unverified whether the matcher
   catches them**; they carry no deliverable content, but the SPEC should say which way it went.

Nothing else. That is the honest answer to "what is still public", and it belongs in the SPEC's
acceptance criteria as a probe, not as a claim.

## Open risks

| # | Risk | How it gets settled |
|---|---|---|
| **R1** | **No root `package.json`.** Vercel's docs place middleware "at the same level as your `package.json`", and the `next()` helper comes from `@vercel/functions`, which nothing installs today | **A preview deployment, before the production domain changes.** Two escapes: **(a)** return `undefined` to continue instead of importing the helper — **unverified, and the failure mode is the bad one**: if it yields an empty 200, authorized visitors get a blank site; **(b)** add a minimal root `package.json` (`"type": "module"` + the one dependency) and adapt `installCommand`. Prefer (b) if (a) does not verify cleanly |
| **R2** | Whether `vercel.json`'s `headers` block applies to a response the middleware authors itself — i.e. whether the login page inherits `X-Robots-Tag` | **Do not rely on it.** Set the header explicitly on the middleware's own `Response` |
| **R3** | Option 3 as sketched puts a **`service_role` key in a Vercel server-side env var** to guard a demo — a full-privilege database key, large blast radius for a small job | Q3 below. The alternative trades it for a public brute-force oracle, so this is a choice between two costs, not a free fix |
| **R4** | Online brute force against the passphrase | Passphrase entropy is the real defence: **four-word diceware, ~50+ bits**. Under Q3(b) an attempts table becomes necessary rather than optional |
| **R5** | `supabase_vault` may not be enabled on the remote project | `select extname from pg_extension where extname = 'supabase_vault'` against `ewknlggenhrlftdukwme`, before the SPEC. If absent, fall back to a `pgcrypto`-hashed row in a locked-down table, or to option 4 |
| **R6** | Middleware now runs on **every** asset request, and is billed on the fluid-compute model | Measure on the preview. If it costs latency that matters, the weaker variant is to gate HTML only and let hashed asset URLs through — **and that is weaker, so it must be said, not silently adopted** |

## Decisions the SPEC has to make

| # | Question | Recommendation |
|---|---|---|
| **Q0** | **Does T1 pass, and is a URL token an acceptable credential?** | **Run it before anything else.** Two yeses and the unit closes here with option 2 — no SPEC, no code. **Q1–Q6 exist only if Q0 is a no.** Do not start on middleware before this is answered |
| **Q1** | Enforcement point | **Edge middleware** — *given Q0 is no*. Not open at that point: the static-file finding forces it |
| **Q2** | Secret store | **Supabase Vault** — *given Q0 is no*. It is the ask, and rotation-without-redeploy is a genuine property rather than a rationalisation |
| **Q3** | How does the middleware authenticate to Supabase? | **(a) RPC granted to `service_role` only**, middleware holds the secret key in a **non-`VITE_`** Vercel env var — no public oracle, but a full-privilege key in Vercel (R3). **(b) RPC granted to `anon`**, middleware uses the publishable key that already ships in the browser bundle — small key, but anyone who reads the bundle gets an unlimited password-guessing endpoint. **Recommend (a)**, blast radius stated rather than netted out. If (b), then R4's entropy floor and an attempts table are both mandatory |
| **Q4** | Session lifetime | **30 days**, HMAC keyed on the passphrase so that rotation revokes |
| **Q5** | One shared passphrase, or per-person accounts? | **One shared passphrase.** State the limitation plainly: **no audit trail, no per-person revocation — revocation is all-or-nothing.** Per-person is option 5, and it is more machinery than a case study warrants |
| **Q6** | What the login page says | Name the case study and the recipient, and **no Groupon branding** — `docs/design/DESIGN-SYSTEM.md` §9's rule against inventing an asset that carries their name applies here more than anywhere, because this page is the first thing they see |

## Constraints

- **Must stay true:** keys never reach the browser bundle. The middleware is server-side; the
  Supabase secret key must be a plain Vercel env var, **never `VITE_`-prefixed** — Vite inlines those.
- **Must stay true:** past the gate, `/explainer.html` renders byte-identically. The gate must not
  become a second copy of, or a wrapper around, the deliverable.
- **Fail closed.** Any error in the Vault read, the RPC, or the HMAC denies access.
- **This unit touches no analysis and produces no number.** Nothing in `FINDINGS.md` moves.
- **The threat model is proportionate, and saying so is part of the proposal.** This keeps the work
  out of search results and stops the link being forwarded casually. The repo holds no personal
  data — the CSVs are synthetic and were supplied by Groupon. It is **not** built to resist a
  determined attacker, and the SPEC should say that in one line rather than imply otherwise.

## Out of scope, stated not deferred

- **Per-person accounts, SSO, audit logging.** Option 5; not built.
- **Protecting preview deployments.** Vercel Authentication at *Standard Protection* is free on every
  plan and covers preview and deployment URLs. **Worth switching on regardless** — it is a separate
  toggle, costs nothing, and is not what this unit is about.
- **Rate limiting beyond whatever Q3 forces.**
- **Any change to Part B's data path**, its grants, or its RLS. Those are already locked down and
  verified (`INDEX.md` 4.1); this gate sits in front of them and changes none of it.

## What would make this brief wrong

- **Returning `undefined` does not continue the chain** → the middleware needs `@vercel/functions` →
  a root `package.json` and a build-config change, and R1 escape (b) becomes the plan rather than the
  fallback.
- **Vault is not available or not readable from a `security definer` function** → the secret moves to
  a `pgcrypto`-hashed row in a locked table, which keeps it in Supabase, or to option 4, which does
  not.
- **T1 comes back protected** → option 2 gates the site today, for free, with no code, and the only
  things option 3 adds are a credential that is not a URL and a secret that lives in Supabase.
  **Decide whether those are worth the hours; the default answer should be no**, because Part C is
  unwritten.
- **The Vercel account already has Pro + Advanced Deployment Protection** → option 1 is less code
  than all of this and should win.
- **Middleware on every asset request measurably slows the explainer** → the approach was too broad;
  gate HTML only and record the weakening.

## Housekeeping this unit exposes

`INDEX.md` 4.4 still reads *"Left: FE hosting on Vercel"*. The site has been live at
`g-demo-six.vercel.app` since at least 2026-08-07 13:52 UTC (`last-modified` on the built bundle).
**A status file that is wrong about what is deployed is the exact drift the repo's own rules
target** — the row is corrected alongside this brief.
