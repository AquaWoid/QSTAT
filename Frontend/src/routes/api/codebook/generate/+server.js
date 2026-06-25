import { env } from '$env/dynamic/private';

const base = () => env.FASTAPI_URL ?? 'http://localhost:8000';
const auth = () => (env.FASTAPI_TOKEN ? { authorization: `Bearer ${env.FASTAPI_TOKEN}` } : {});

export async function PUT({ request }) {
  const body = await request.json();
  const r = await fetch(`${base()}/codebook/generate`, {
    method: 'PUT',
    headers: { 'content-type': 'application/json', ...auth() },
    body: JSON.stringify(body)
  });
  return new Response(r.body, {
    status: r.status,
    headers: { 'content-type': r.headers.get('content-type') ?? 'application/json' }
  });
}
