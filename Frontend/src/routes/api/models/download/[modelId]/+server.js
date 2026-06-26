import { env } from '$env/dynamic/private';

export async function GET({ params }) {
  const { modelId } = params;

  const upstream = await fetch(
    `${env.FASTAPI_URL ?? 'http://localhost:8000'}/models/download/${modelId}`,
    {
      headers: {
        accept: 'text/event-stream',
        ...(env.FASTAPI_TOKEN ? { authorization: `Bearer ${env.FASTAPI_TOKEN}` } : {})
      }
    }
  );

  if (!upstream.ok || !upstream.body) {
    return new Response(`upstream error: ${upstream.status}`, { status: 502 });
  }

  return new Response(upstream.body, {
    headers: {
      'content-type': 'text/event-stream',
      'cache-control': 'no-cache, no-transform',
      connection: 'keep-alive',
      'x-accel-buffering': 'no'
    }
  });
}
