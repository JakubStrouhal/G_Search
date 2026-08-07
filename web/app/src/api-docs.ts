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
const specResponse = await fetch(`${url}/rest/v1/`, {
  headers: { apikey: publishableKey },
})
if (!specResponse.ok) {
  throw new Error(`Spec fetch failed: ${specResponse.status} ${specResponse.statusText}`)
}
const spec = await specResponse.json()
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
