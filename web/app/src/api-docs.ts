import SwaggerUI from 'swagger-ui-dist/swagger-ui-es-bundle.js'
import 'swagger-ui-dist/swagger-ui.css'
import '@design/outputs/tokens.css'
import './styles/api-docs.css'

// Same env contract as config/supabase.ts, but WITHOUT importing the client:
// this entry ships Swagger UI (~large) and nothing else — pulling in
// supabase-js here would be dead weight on a documentation page.
const url = import.meta.env.VITE_SUPABASE_URL
const publishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY

if (!url || !publishableKey) {
  throw new Error(
    'Missing VITE_SUPABASE_URL or VITE_SUPABASE_PUBLISHABLE_KEY. ' +
      'Copy web/app/.env.local from .env.example and fill it from `npx supabase status`.',
  )
}

// PostgREST reports its OWN listen address in the spec (host: 0.0.0.0:3000 —
// its position behind Supabase's gateway is invisible to it), so "Try it out"
// would aim past the gateway and fail. Fetch the spec, repoint host/basePath/
// schemes at the gateway, and hand Swagger UI the patched object.
//
// WHERE the spec comes from differs by environment. Hosted Supabase serves the
// OpenAPI root to secret keys only (observed 2026-08-07: 401 "Secret API key
// required" for publishable keys — data endpoints are unaffected). The secret
// key cannot ship to the browser, so in production the spec comes from this
// deployment's own middleware at /__spec, which holds the secret server-side
// and sits behind the same access gate as this page. The local stack has no
// middleware and no such restriction, so dev fetches PostgREST directly.
const escapeHtml = (s: string) => s.replace(/[&<>"]/g, (c) => `&#${c.charCodeAt(0)};`)

// A thrown error alone renders as a blank page — and so, in practice, did the bare
// paragraph that used to live here: under a full-height header it read as nothing at
// all, and a live 502 on this page went unnoticed because of it. So the failure gets
// the same weight as the content it replaces: an alert panel, in the page's own
// column, naming the cause. This page's whole claim is honesty about state, which is
// worth least at the moment there is no state to show.
//
// `detail` is upstream text, so it is escaped before it reaches innerHTML.
function fail(reason: string, detail?: string): never {
  document.querySelector('#swagger-ui')!.innerHTML =
    `<div class="spec-failure" role="alert">` +
    `<h2>The live OpenAPI spec could not be fetched</h2>` +
    `<p>${escapeHtml(reason)}</p>` +
    (detail ? `<p class="detail">Supabase said: <code>${escapeHtml(detail)}</code></p>` : '') +
    // Label and href must agree. The old link said `/app` and went to `/app` — the
    // package index, not the prototype — which is the same mis-aim api.html's
    // deliverables bar was rewritten to remove. Pointing it at /app#prototype while
    // still *reading* `/app` would only invert the lie.
    `<p>The API itself is unaffected — the prototype at ` +
    `<a href="/app#prototype">/app#prototype</a> talks to it directly. ` +
    `Only this documentation page needs the spec.</p>` +
    `</div>`
  throw new Error(`Spec fetch failed: ${reason}${detail ? ` — ${detail}` : ''}`)
}

const specResponse = import.meta.env.DEV
  ? await fetch(`${url}/rest/v1/`, { headers: { apikey: publishableKey } })
  : await fetch('/__spec')
// Read once: the body is the error detail on a failure and the spec on success.
const body = await specResponse.text()

if (!specResponse.ok) {
  // Both error shapes are JSON: `{upstream, upstreamStatus}` from this deployment's
  // proxy, `{message}` straight from Supabase's gateway on the dev path.
  let detail: string | undefined
  let upstreamStatus: number | undefined
  try {
    const parsed = JSON.parse(body)
    detail = typeof parsed?.upstream === 'string' ? parsed.upstream
      : typeof parsed?.message === 'string' ? parsed.message
      : undefined
    upstreamStatus = typeof parsed?.upstreamStatus === 'number' ? parsed.upstreamStatus : undefined
  } catch {
    // Non-JSON error body — the status is all there is.
  }
  if (specResponse.status === 503) {
    fail('This deployment has no server-side SUPABASE_SECRET_KEY set, and the hosted spec endpoint accepts nothing else.', detail)
  }
  if (specResponse.status === 502) {
    fail(
      upstreamStatus === 401 || upstreamStatus === 403
        ? 'Supabase rejected this deployment’s SUPABASE_SECRET_KEY: the value configured here is not a valid secret key for this project. Re-adding it and redeploying fixes the page — middleware environment is baked per deployment.'
        : `This deployment reached Supabase, which answered HTTP ${upstreamStatus ?? 'an error'} instead of the spec.`,
      detail,
    )
  }
  fail(`The spec endpoint answered HTTP ${specResponse.status}.`, detail)
}
// Parse defensively: a server that answers /__spec with an HTML fallback (any
// static host without the middleware, e.g. `vite preview`) returns 200 + HTML.
let spec
try {
  spec = JSON.parse(body)
} catch {
  fail('The spec endpoint answered with something that is not JSON — likely a static host serving this page without the middleware that proxies the spec.')
}
const gateway = new URL(url)
spec.host = gateway.host
spec.basePath = '/rest/v1'
spec.schemes = [gateway.protocol.replace(':', '')]

// The publishable key is the browser key — it already ships in the app bundle,
// so attaching it here exposes nothing new. It is what makes "Try it out"
// execute for real: Supabase's gateway rejects requests without an apikey.
SwaggerUI({
  dom_id: '#swagger-ui',
  spec,
  requestInterceptor: (req) => {
    req.headers['apikey'] = publishableKey
    req.headers['Authorization'] = `Bearer ${publishableKey}`
    return req
  },
  // The spec is one flat list of paths; sort it so tables, views and /rpc/*
  // group visually instead of landing in schema-definition order.
  operationsSorter: 'alpha',
  tagsSorter: 'alpha',
  defaultModelsExpandDepth: 0,
})
