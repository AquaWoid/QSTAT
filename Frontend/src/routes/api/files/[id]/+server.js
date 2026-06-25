import { env } from '$env/dynamic/private';

const base = () => env.FASTAPI_URL ?? 'http://localhost:8000';
const auth = () => (env.FASTAPI_TOKEN ? { authorization: `Bearer ${env.FASTAPI_TOKEN}` } : {});

export async function DELETE({ params }) {
  const r = await fetch(`${base()}/files/${params.id}`, {
    method: 'DELETE',
    headers: auth()
  });
  return new Response(r.body, {
    status: r.status,
    headers: { 'content-type': r.headers.get('content-type') ?? 'application/json' }
  });
}
