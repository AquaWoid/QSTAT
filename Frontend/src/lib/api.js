// Client-side API helpers. These call the SvelteKit `+server.js` proxy routes
// under `/api/*`, which in turn forward to FastAPI. Keeping the FastAPI URL
// and any tokens off the browser.

/**
 * Stream a chat completion. Yields events as they arrive over SSE.
 * @param {{ messages: Array<{role:string,content:string}>, model:string, rag?:{on:boolean,scope:string} }} body
 * @returns {AsyncGenerator<{type:'token'|'cite'|'done', value?:any}>}
 */
export async function* streamChat(body) {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok || !res.body) throw new Error(`chat failed: ${res.status}`);

  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let nl;
    while ((nl = buf.indexOf('\n\n')) !== -1) {
      const event = buf.slice(0, nl);
      buf = buf.slice(nl + 2);
      const dataLine = event.split('\n').find((l) => l.startsWith('data:'));
      if (!dataLine) continue;
      const payload = dataLine.slice(5).trim();
      if (!payload || payload === '[DONE]') {
        yield { type: 'done' };
        continue;
      }
      try {
        yield JSON.parse(payload);
      } catch {
        yield { type: 'token', value: payload };
      }
    }
  }
}

export async function uploadFile(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch('/api/files', { method: 'POST', body: form });
  if (!res.ok) throw new Error(`upload failed: ${res.status}`);
  return res.json();
}

export async function listFiles() {
  const res = await fetch('/api/files');
  if (!res.ok) throw new Error(`list failed: ${res.status}`);
  return res.json();
}

export async function deleteFile(id) {
  const res = await fetch(`/api/files/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`delete failed: ${res.status}`);
  return res.json();
}

export async function getTranscript(fileId) {
  const res = await fetch(`/api/files/${fileId}/transcript`);
  if (!res.ok) throw new Error(`transcript failed: ${res.status}`);
  return res.json();
}

export async function transcribe(fileId) {
  const res = await fetch('/api/transcribe', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ fileId })
  });
  if (!res.ok) throw new Error(`transcribe failed: ${res.status}`);
  return res.json();
}

export async function transcribeStatus(jobId) {
  const res = await fetch(`/api/transcribe/status/${jobId}`);
  if (!res.ok) throw new Error(`status failed: ${res.status}`);
  return res.json();
}

export async function getCodebook() {
  const res = await fetch('/api/codebook');
  if (!res.ok) throw new Error(`codebook failed: ${res.status}`);
  return res.json();
}

export async function saveCodebook(codebook) {
  const res = await fetch('/api/codebook', {
    method: 'PUT',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(codebook)
  });
  if (!res.ok) throw new Error(`save codebook failed: ${res.status}`);
  return res.json();
}

export async function updateTranscript(fileId, turns) {
  const res = await fetch(`/api/files/${fileId}/transcript`, {
    method: 'PATCH',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ turns })
  });
  if (!res.ok) throw new Error(`transcript update failed: ${res.status}`);
  return res.json();
}

export async function generateCodebook(transcript) {
  const res = await fetch('/api/codebook/generate', {
    method: 'PUT',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ transcript })
  });
  if (!res.ok) throw new Error(`generate codebook failed: ${res.status}`);
  return res.json();
}

export async function suggestCodes(transcriptId, existing) {
  const res = await fetch('/api/codebook', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ transcriptId, existing })
  });
  if (!res.ok) throw new Error(`suggest failed: ${res.status}`);
  return res.json();
}

export async function fetchModels() {
  const res = await fetch('/api/models');
  if (!res.ok) throw new Error(`models failed: ${res.status}`);
  return res.json();
}

export async function fetchConfig() {
  const res = await fetch('/api/config');
  if (!res.ok) throw new Error(`config failed: ${res.status}`);
  return res.json();
}

export async function patchConfig(patch) {
  const res = await fetch('/api/config', {
    method: 'PATCH',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(patch)
  });
  if (!res.ok) throw new Error(`config save failed: ${res.status}`);
  return res.json();
}
