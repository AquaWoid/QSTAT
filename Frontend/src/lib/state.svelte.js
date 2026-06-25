// QualScope app state — Svelte 5 runes.
//
// All cross-component state lives here. Components import `app` and read/write
// its fields directly; reactivity flows through the rune-based getters/setters.

import { PROJECT, CODEBOOK, CITES } from './data.js';

const KEY = 'qualscope.tweaks.v1';

function loadTweaks() {
  if (typeof localStorage === 'undefined') return null;
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? 'null');
  } catch {
    return null;
  }
}

function saveTweaks(t) {
  if (typeof localStorage === 'undefined') return;
  localStorage.setItem(KEY, JSON.stringify(t));
}

const TWEAK_DEFAULTS = {
  dark: false,
  accent: '#9a3a2e',
  font: 'newsreader-plex',
  wContext: 220,
  wCodebook: 280,
  wChat: 340,
  showContext: true,
  showChat: true
};

export const ACCENTS_LIGHT = ['#9a3a2e', '#345a91', '#3f6b4a', '#6b3a6e'];
export const ACCENTS_DARK  = ['#d97a6c', '#7fa4d9', '#86b896', '#b48cb6'];

let _toastSeq = 0;

function createState() {
  // Files are populated on mount by ContextPane; start empty to avoid spurious poll.
  let files     = $state(/** @type {typeof PROJECT.files} */ ([]));
  let codebook  = $state(CODEBOOK);

  // Citation registry — mutable object so MessageStream can add entries.
  // Initialised with demo cites; live cites accumulate with higher IDs.
  let cites = $state({ ...CITES });

  let activeFile = $state(/** @type {string | null} */ (null));
  let activeCode = $state(/** @type {string | null} */ (null));
  let citeFlash  = $state(/** @type {number | null} */ (null));
  /** Turn ID to scroll to after a transcript loads — set by cite() for transcript chunks. */
  let pendingTurnScroll = $state(/** @type {string | null} */ (null));

  let tweaks = $state({ ...TWEAK_DEFAULTS, ...(loadTweaks() ?? {}) });
  let tweaksOpen = $state(false);

  // Chat thread — array of {role, content, id, ts, citeIds?}
  let messages = $state(/** @type {Array<{role:string,content:string,id:string,ts:string,citeIds?:number[]}>} */ ([]));

  // Toast notifications — array of {id, msg, kind}
  let toasts = $state(/** @type {Array<{id:number,msg:string,kind:'error'|'info'}>} */ ([]));

  let researchQuestion = $state('');
  let highlightRQ = $state(false);

  return {
    // ── Files ──────────────────────────────────────────────────────────────
    get files()     { return files; },
    set files(v)    { files = v; },

    // ── Codebook ───────────────────────────────────────────────────────────
    get codebook()  { return codebook; },
    set codebook(v) { codebook = v; },

    // ── Cites ──────────────────────────────────────────────────────────────
    get cites()     { return cites; },
    /** Register a cite object (called by MessageStream as SSE events arrive). */
    registerCite(id, cite) {
      cites[id] = cite;
    },

    // ── Active state ───────────────────────────────────────────────────────
    get activeFile()   { return activeFile; },
    set activeFile(v)  { activeFile = v; },
    get activeCode()   { return activeCode; },
    set activeCode(v)  { activeCode = v; },
    get citeFlash()    { return citeFlash; },
    set citeFlash(v)   { citeFlash = v; },
    get pendingTurnScroll()  { return pendingTurnScroll; },
    set pendingTurnScroll(v) { pendingTurnScroll = v; },

    // ── Tweaks ─────────────────────────────────────────────────────────────
    get tweaksOpen()      { return tweaksOpen; },
    set tweaksOpen(v)     { tweaksOpen = v; },
    toggleTweaks()        { tweaksOpen = !tweaksOpen; },

    get tweaks()  { return tweaks; },
    setTweak(key, value) {
      tweaks = { ...tweaks, [key]: value };
      saveTweaks(tweaks);
    },

    // ── Messages (chat thread) ─────────────────────────────────────────────
    get messages()     { return messages; },
    pushMessage(m)     { messages = [...messages, m]; },
    clearMessages()    { messages = []; },
    /** Save streamed content + cites to a specific message, mark it done. */
    finalizeMessage(id, content, citeIds) {
      messages = messages.map((m) =>
        m.id === id ? { ...m, content, citeIds, streaming: false } : m
      );
    },

    // ── Toasts ─────────────────────────────────────────────────────────────
    get toasts()  { return toasts; },
    toast(msg, kind = 'error') {
      const id = ++_toastSeq;
      toasts = [...toasts, { id, msg, kind }];
      setTimeout(() => {
        toasts = toasts.filter((t) => t.id !== id);
      }, 4000);
    },
    dismissToast(id) {
      toasts = toasts.filter((t) => t.id !== id);
    },

    // ── Research context ───────────────────────────────────────────────────
    get researchQuestion()  { return researchQuestion; },
    set researchQuestion(v) { researchQuestion = v; },
    get highlightRQ()       { return highlightRQ; },
    set highlightRQ(v)      { highlightRQ = v; },

    // ── Citation click ─────────────────────────────────────────────────────
    /** Click a citation chip — jumps to transcript turn or highlights file. */
    cite(id) {
      citeFlash = id;
      const c = cites[id];
      if (c?.kind === 'd' && c.fileId) {
        if (c.turnId) {
          // Transcript chunk: switch file (if needed) then scroll to turn.
          if (activeFile !== c.fileId) {
            // TranscriptPane will pick up pendingTurnScroll after loading.
            pendingTurnScroll = c.turnId;
            activeFile = c.fileId;
          } else {
            // File already loaded — scroll immediately.
            pendingTurnScroll = c.turnId;
          }
        } else {
          activeFile = c.fileId;
        }
      } else if (typeof document !== 'undefined') {
        queueMicrotask(() => {
          const el = document.querySelector(`[data-cite="${id}"]`);
          if (el) {
            const container = el.closest('.pane-body');
            if (container) {
              const rect = el.getBoundingClientRect();
              const cRect = container.getBoundingClientRect();
              container.scrollTop += rect.top - cRect.top - 200;
            }
          }
        });
      }
      setTimeout(() => { citeFlash = null; }, 1800);
    }
  };
}

export const app = createState();

// ── Template helpers ──────────────────────────────────────────────────────────

export function codeColor(codebook, codeId) {
  for (const g of codebook) for (const c of g.children) if (c.id === codeId) return c.color;
  return '1';
}

export function fmtTime(secs) {
  const s = Math.max(0, Math.floor(secs));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return `${String(m).padStart(2, '0')}:${String(r).padStart(2, '0')}`;
}
