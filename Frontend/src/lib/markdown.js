/**
 * Minimal markdown parser for LLM output.
 * Returns a Block[] that Svelte templates can render with Citation chips intact.
 *
 * Block types:
 *   {kind:'p'|'h3'|'h4'|'bq', parts: InlinePart[]}
 *   {kind:'ul'|'ol', items: InlinePart[][]}
 *
 * InlinePart types:
 *   {kind:'text', value:string}   – plain text, may contain **bold** / *italic* / `code`
 *   {kind:'cite', id:number}      – [^N] citation chip
 */

/** Escape HTML special chars in a raw string before injecting bold/italic markup. */
function escHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

/** Apply inline formatting to a plain-text string → HTML fragment (safe to {@html}). */
export function inlineHtml(text) {
  return escHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*\n]+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+?)`/g, '<code>$1</code>');
}

/**
 * Split a string into text parts and [^N] citation markers.
 * @returns {Array<{kind:'text',value:string}|{kind:'cite',id:number}>}
 */
export function parseCites(text) {
  const parts = [];
  const re = /\[\^(\d+)\]/g;
  let last = 0;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push({ kind: 'text', value: text.slice(last, m.index) });
    parts.push({ kind: 'cite', id: Number(m[1]) });
    last = m.index + m[0].length;
  }
  if (last < text.length) parts.push({ kind: 'text', value: text.slice(last) });
  return parts;
}

/**
 * Parse markdown text into an array of typed blocks.
 */
export function parseBlocks(text) {
  const blocks = [];
  // Split on blank lines
  const rawBlocks = text.split(/\n{2,}/);

  for (const raw of rawBlocks) {
    const trimmed = raw.trim();
    if (!trimmed) continue;

    const lines = trimmed.split('\n');
    const first = lines[0];

    if (/^### /.test(first)) {
      blocks.push({ kind: 'h4', parts: parseCites(first.replace(/^### /, '')) });
    } else if (/^## /.test(first)) {
      blocks.push({ kind: 'h3', parts: parseCites(first.replace(/^## /, '')) });
    } else if (/^# /.test(first)) {
      blocks.push({ kind: 'h3', parts: parseCites(first.replace(/^# /, '')) });
    } else if (lines.every((l) => /^[-*] /.test(l.trim()) || !l.trim())) {
      blocks.push({
        kind: 'ul',
        items: lines.filter((l) => l.trim()).map((l) => parseCites(l.replace(/^[-*] /, '')))
      });
    } else if (lines.every((l) => /^\d+\. /.test(l.trim()) || !l.trim())) {
      blocks.push({
        kind: 'ol',
        items: lines.filter((l) => l.trim()).map((l) => parseCites(l.replace(/^\d+\. /, '')))
      });
    } else if (/^> /.test(first)) {
      const inner = lines.map((l) => l.replace(/^> ?/, '')).join(' ');
      blocks.push({ kind: 'bq', parts: parseCites(inner) });
    } else {
      // Collapse single newlines within a paragraph to spaces
      blocks.push({ kind: 'p', parts: parseCites(lines.join(' ')) });
    }
  }

  return blocks;
}
