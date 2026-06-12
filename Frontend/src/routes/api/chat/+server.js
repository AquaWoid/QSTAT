/**
 * SSE proxy for the chat endpoint.
 *
 * The browser hits /api/chat → this handler forwards to FASTAPI_URL/chat
 * with the bearer token (if any) and pipes the SSE stream back. The
 * FastAPI URL and token never reach the client.
 */
import { env } from '$env/dynamic/private';

export async function POST({ request }) {
  const body = await request.json();

  const upstream = await fetch(`${env.FASTAPI_URL ?? 'http://localhost:8001'}/chat`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      accept: 'text/event-stream',
      ...(env.FASTAPI_TOKEN ? { authorization: `Bearer ${env.FASTAPI_TOKEN}` } : {})
    },
    body: JSON.stringify(body)
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
