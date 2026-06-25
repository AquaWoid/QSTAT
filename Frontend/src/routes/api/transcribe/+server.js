/**
 * Transcribe proxy.
 * POST /api/transcribe  → kicks off ASR for a fileId. Returns 202 + a job ID.
 *
 * If your FastAPI streams progress over SSE, swap to the streaming pattern
 * used in /api/chat. For simple "start job" semantics, this is enough.
 */
import { env } from '$env/dynamic/private';

export async function POST({ request }) {
  const body = await request.json();
  const r = await fetch(`${env.FASTAPI_URL ?? 'http://localhost:8000'}/transcribe`, {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      ...(env.FASTAPI_TOKEN ? { authorization: `Bearer ${env.FASTAPI_TOKEN}` } : {})
    },
    body: JSON.stringify(body)
  });
  return new Response(r.body, {
    status: r.status,
    headers: { 'content-type': r.headers.get('content-type') ?? 'application/json' }
  });
}
