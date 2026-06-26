import { env } from '$env/dynamic/private';

export async function GET() {
  const upstream = await fetch(`${env.FASTAPI_URL ?? 'http://localhost:8000'}/models/status`, {
    headers: {
      ...(env.FASTAPI_TOKEN ? { authorization: `Bearer ${env.FASTAPI_TOKEN}` } : {})
    }
  });

  if (!upstream.ok) {
    return new Response(`upstream error: ${upstream.status}`, { status: 502 });
  }

  const data = await upstream.json();
  return new Response(JSON.stringify(data), {
    headers: { 'content-type': 'application/json' }
  });
}
