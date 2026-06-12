import { env } from '$env/dynamic/private';

const base = () => env.FASTAPI_URL ?? 'http://localhost:8001';
const auth = () => (env.FASTAPI_TOKEN ? { authorization: `Bearer ${env.FASTAPI_TOKEN}` } : {});

export async function GET() {
  const r = await fetch(`${base()}/codebook`, { headers: auth() });
  return new Response(r.body, {
    status: r.status,
    headers: { 'content-type': r.headers.get('content-type') ?? 'application/json' }
  });
}

export async function PUT({ request }) {
  const body = await request.json();
  const r = await fetch(`${base()}/codebook`, {
    method: 'PUT',
    headers: { 'content-type': 'application/json', ...auth() },
    body: JSON.stringify(body)
  });
  return new Response(r.body, {
    status: r.status,
    headers: { 'content-type': r.headers.get('content-type') ?? 'application/json' }
  });
}

export async function POST({ request }) {
  // Used by "✦ Suggest codes" — sends current transcript context, gets back
  // proposed codes from the LLM.
  const body = await request.json();
  const r = await fetch(`${base()}/codebook/suggest`, {
    method: 'POST',
    headers: { 'content-type': 'application/json', ...auth() },
    body: JSON.stringify(body)
  });
  return new Response(r.body, {
    status: r.status,
    headers: { 'content-type': r.headers.get('content-type') ?? 'application/json' }
  });
}
