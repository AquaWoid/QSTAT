/**
 * Files proxy — list + upload.
 * GET  /api/files          → list (forwards GET to FastAPI /files)
 * POST /api/files          → upload (forwards multipart to FastAPI /files)
 */
import { env } from '$env/dynamic/private';

const base = () => env.FASTAPI_URL ?? 'http://localhost:8001';
const auth = () => (env.FASTAPI_TOKEN ? { authorization: `Bearer ${env.FASTAPI_TOKEN}` } : {});

export async function GET() {
  const r = await fetch(`${base()}/files`, { headers: auth() });
  return new Response(r.body, {
    status: r.status,
    headers: { 'content-type': r.headers.get('content-type') ?? 'application/json' }
  });
}

export async function POST({ request }) {
  // Forward the multipart body straight through.
  const form = await request.formData();
  const r = await fetch(`${base()}/files`, {
    method: 'POST',
    headers: auth(),
    body: form
  });
  return new Response(r.body, {
    status: r.status,
    headers: { 'content-type': r.headers.get('content-type') ?? 'application/json' }
  });
}
