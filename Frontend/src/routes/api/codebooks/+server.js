import { env } from '$env/dynamic/private';

const base = () => env.FASTAPI_URL ?? 'http://localhost:8000';
const auth = () => (env.FASTAPI_TOKEN ? { authorization: `Bearer ${env.FASTAPI_TOKEN}` } : {});

export async function GET() {
  const r = await fetch(`${base()}/codebooks`, { headers: auth() });
  return new Response(r.body, {
    status: r.status,
    headers: { 'content-type': r.headers.get('content-type') ?? 'application/json' }
  });
}
