import { env } from '$env/dynamic/private';

const UPSTREAM = () => env.FASTAPI_URL ?? 'http://localhost:8001';
const AUTH = () => env.FASTAPI_TOKEN ? { authorization: `Bearer ${env.FASTAPI_TOKEN}` } : {};

export async function GET() {
  const upstream = await fetch(`${UPSTREAM()}/config`, { headers: AUTH() });
  if (!upstream.ok) return new Response(`upstream error: ${upstream.status}`, { status: 502 });
  return new Response(await upstream.text(), { headers: { 'content-type': 'application/json' } });
}

export async function PATCH({ request }) {
  const body = await request.json();
  const upstream = await fetch(`${UPSTREAM()}/config`, {
    method: 'PATCH',
    headers: { 'content-type': 'application/json', ...AUTH() },
    body: JSON.stringify(body)
  });
  if (!upstream.ok) return new Response(`upstream error: ${upstream.status}`, { status: 502 });
  return new Response(await upstream.text(), { headers: { 'content-type': 'application/json' } });
}
