// Minimal shim for the ES bundle subpath — @types/swagger-ui-dist covers the
// package root only, and we import the subpath to get the ESM build. Typed to
// the option subset this app actually passes.
declare module 'swagger-ui-dist/swagger-ui-es-bundle.js' {
  interface SwaggerUIRequest {
    headers: Record<string, string>
    url: string
  }
  interface SwaggerUIOptions {
    dom_id: string
    url?: string
    spec?: object
    requestInterceptor?: (req: SwaggerUIRequest) => SwaggerUIRequest
    operationsSorter?: 'alpha' | 'method'
    tagsSorter?: 'alpha'
    defaultModelsExpandDepth?: number
  }
  const SwaggerUI: (options: SwaggerUIOptions) => unknown
  export default SwaggerUI
}
