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
// A thrown error alone renders as a blank page. Say what failed where the
// spec was meant to appear — this page's whole claim is honesty about state.
function fail(reason: string): never {
  document.querySelector('#swagger-ui')!.innerHTML =
    `<p style="max-width:60ch;margin:2rem auto;font:15px/1.5 sans-serif">` +
    `The live OpenAPI spec could not be fetched. ${reason} ` +
    `The API itself is unaffected — the prototype at <a href="/app">/app</a> talks to it directly.</p>`
  throw new Error(`Spec fetch failed: ${reason}`)
}

const specResponse = import.meta.env.DEV
  ? await fetch(`${url}/rest/v1/`, { headers: { apikey: publishableKey } })
  : await fetch('/__spec')
if (!specResponse.ok) {
  fail(
    `HTTP ${specResponse.status}.` +
      (specResponse.status === 503
        ? ' The deployment is missing its server-side SUPABASE_SECRET_KEY, which the hosted spec endpoint requires.'
        : ''),
  )
}
// Parse defensively: a server that answers /__spec with an HTML fallback (any
// static host without the middleware, e.g. `vite preview`) returns 200 + HTML.
let spec
try {
  spec = JSON.parse(await specResponse.text())
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
