import { env } from '$env/dynamic/private';

const base = () => env.FASTAPI_URL ?? 'http://localhost:8001';
const auth = () => (env.FASTAPI_TOKEN ? { authorization: `Bearer ${env.FASTAPI_TOKEN}` } : {});

export async function GET({ params, request }) {
  const headers = { ...auth() };
  const range = request.headers.get('range');
  if (range) headers['range'] = range;

  const r = await fetch(`${base()}/files/${params.id}/pdf`, { headers });

  const resHeaders = { 'accept-ranges': 'bytes', 'content-type': 'application/pdf' };
  const cl = r.headers.get('content-length');
  if (cl) resHeaders['content-length'] = cl;
  const cr = r.headers.get('content-range');
  if (cr) resHeaders['content-range'] = cr;

  return new Response(r.body, { status: r.status, headers: resHeaders });
}
