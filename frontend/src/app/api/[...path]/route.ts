import { randomUUID } from "node:crypto";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  const started = performance.now();
  const proxyId = randomUUID();
  const { path } = await context.params;
  const headers = new Headers({ "X-Proxy-Request-ID": proxyId });
  for (const name of ["content-type", "accept"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }
  const base = (process.env.BACKEND_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
  const target = new URL(`${base}/api/${path.map(encodeURIComponent).join("/")}`);
  target.search = new URL(request.url).search;
  let status = 502;
  let requestId: string | null = null;
  try {
    const upstream = await fetch(target, {
      method: request.method, headers, cache: "no-store", redirect: "error",
      body: ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer(),
      signal: AbortSignal.timeout(180_000),
    });
    status = upstream.status;
    requestId = upstream.headers.get("X-Request-ID");
    const outgoing = new Headers({ "Cache-Control": "no-store", "X-Proxy-Request-ID": proxyId });
    for (const name of ["content-type", "x-request-id", "server-timing"]) {
      const value = upstream.headers.get(name);
      if (value) outgoing.set(name, value);
    }
    outgoing.append("Server-Timing", `proxy;dur=${(performance.now() - started).toFixed(1)}`);
    return new Response(upstream.body, { status, headers: outgoing });
  } catch {
    return Response.json({ detail: "The backend could not be reached. Check that the API is running, then retry." }, {
      status, headers: { "X-Proxy-Request-ID": proxyId, "Cache-Control": "no-store" },
    });
  } finally {
    // Route templates keep user text, query strings and credentials out of logs.
    const route = path.map(part => /^[0-9a-f-]{32,36}$/i.test(part) ? ":id" : /^[a-z-]+$/.test(part) ? part : ":value").join("/");
    console.info(JSON.stringify({ event: "proxy_request", method: request.method, route: `/api/${route}`, status,
      duration_ms: Math.round(performance.now() - started), proxy_request_id: proxyId, request_id: requestId }));
  }
}

export { proxy as GET, proxy as POST, proxy as PUT, proxy as PATCH, proxy as DELETE, proxy as HEAD, proxy as OPTIONS };
