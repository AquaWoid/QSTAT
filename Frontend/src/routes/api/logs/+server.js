/**
 * SSE proxy for the log stream.
 *
 * The browser hits /api/logs (via EventSource) → this handler forwards to
 * FASTAPI_URL/logs and pipes the SSE stream back. The FastAPI URL and token
 * never reach the client.
 */
import { env } from '$env/dynamic/private';

export async function GET() {
  const upstream = await fetch(`${env.FASTAPI_URL ?? 'http://localhost:8000'}/logs`, {
    headers: {
      accept: 'text/event-stream',
      ...(env.FASTAPI_TOKEN ? { authorization: `Bearer ${env.FASTAPI_TOKEN}` } : {})
    }
  });

  if (!upstream.ok || !upstream.body) {
    return new Response(`upstream error: ${upstream.status}`, { status: 502 });
  }

  return new Response(upstream.body, {
    headers: {
      'content-type': 'text/event-stream',
      'cache-control': 'no-cache, no-transform',
      connection: 'keep-alive',
      'x-accel-buffering': 'no'
    }
  });
}
