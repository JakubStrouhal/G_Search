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
const LOGOUT_PATH = '/__gate/logout'
const SPEC_PATH = '/__spec'
const TTL_SECONDS = 30 * 24 * 60 * 60

/**
 * Every attribute except Max-Age must match the Set-Cookie that issued it, Path=/ above
 * all: scoped to /__gate/logout the deletion applies to a cookie the browser never had,
 * the real one survives, and logout silently does nothing.
 */
const COOKIE_ATTRS = `Path=/; HttpOnly; Secure; SameSite=Lax`

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

  // Before the valid-cookie check below, not after: a signed-in visitor is exactly the
  // one asking to sign out, and next() would hand /__gate/logout to the static output
  // as a 404. POST only — a GET logout fires from any <img> on any page.
  //
  // This forgets the session on this browser; it does not revoke it. The cookie is
  // self-contained, so a copy taken off this machine stays valid until it expires.
  // Rotating SITE_PASSWORD is still the only thing that invalidates issued cookies.
  if (url.pathname === LOGOUT_PATH) {
    // Anything but POST gets the same 401 form every other path gets. A 405 here would
    // be the honest status code and the wrong one: SPEC §B1 is that the unauthenticated
    // response is uniform, and a status only this path returns names it to a prober.
    // The form targets `/`, not this path — targeting itself would loop through login.
    if (request.method !== 'POST') return page('/', 401, false)

    return new Response(null, {
      status: 303,
      headers: {
        location: '/',
        // A cached Set-Cookie is the other way this fails without a symptom.
        'cache-control': 'no-store',
        'set-cookie': `${COOKIE}=; Max-Age=0; ${COOKIE_ATTRS}`,
      },
    })
  }

  if (await cookieIsValid(readCookie(request.headers.get('cookie'), COOKIE), secret)) {
    // Spec proxy for /api. Hosted Supabase serves the PostgREST OpenAPI root to
    // SECRET keys only ("Secret API key required" — observed 2026-08-07; publishable
    // keys still reach every data endpoint). The secret key must never ship to the
    // browser, so the browser asks THIS deployment, and the fetch with the secret
    // happens here, server-side. Inside the valid-cookie branch deliberately: an
    // unauthenticated request for /__spec falls through to the uniform 401 form,
    // same as every other path (009-access-gate SPEC §B1).
    if (url.pathname === SPEC_PATH) {
      const supabaseUrl = process.env.VITE_SUPABASE_URL
      const secretKey = process.env.SUPABASE_SECRET_KEY
      if (!supabaseUrl || !secretKey) {
        return new Response(
          JSON.stringify({ error: 'Spec proxy not configured: SUPABASE_SECRET_KEY is unset on this deployment.' }),
          { status: 503, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } },
        )
      }
      const upstream = await fetch(`${supabaseUrl}/rest/v1/`, {
        headers: { apikey: secretKey, Authorization: `Bearer ${secretKey}` },
      })
      if (!upstream.ok) {
        return new Response(
          JSON.stringify({ error: `Upstream spec fetch failed: ${upstream.status}` }),
          { status: 502, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } },
        )
      }
      return new Response(await upstream.text(), {
        status: 200,
        headers: { 'content-type': 'application/openapi+json', 'cache-control': 'no-store' },
      })
    }
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
          'set-cookie': `${COOKIE}=${value}; Max-Age=${TTL_SECONDS}; ${COOKIE_ATTRS}`,
        },
      })
    }
    return page(target, 401, true)
  }

  return page(url.pathname + url.search, 401, false)
}
