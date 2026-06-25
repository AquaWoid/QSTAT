import { env } from '$env/dynamic/private';

const base = () => env.FASTAPI_URL ?? 'http://localhost:8000';
const auth = () => (env.FASTAPI_TOKEN ? { authorization: `Bearer ${env.FASTAPI_TOKEN}` } : {});

export async function GET({ params }) {
  const r = await fetch(`${base()}/files/${params.id}/transcript`, { headers: auth() });
  return new Response(r.body, {
    status: r.status,
    headers: { 'content-type': r.headers.get('content-type') ?? 'application/json' }
  });
}

export async function PATCH({ params, request }) {
  const body = await request.json();
  const r = await fetch(`${base()}/files/${params.id}/transcript`, {
    method: 'PATCH',
    headers: { 'content-type': 'application/json', ...auth() },
    body: JSON.stringify(body)
  });
  return new Response(r.body, {
    status: r.status,
    headers: { 'content-type': r.headers.get('content-type') ?? 'application/json' }
  });
}
