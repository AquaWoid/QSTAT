# QualScope — SvelteKit frontend

Qualitative data analysis interface with four panes: project context, transcript
editor, codebook, chat. Built on SvelteKit + Svelte 5 runes. Plain CSS, no
Tailwind, no UI library.

## Setup

```bash
cd sveltekit
cp .env.example .env        # set FASTAPI_URL
npm install
npm run dev
```

Open `http://localhost:5173`. The frontend talks to its own `/api/*` routes,
which proxy to your FastAPI server. The FastAPI URL and token never reach the
browser.

## Architecture

```
src/
├── app.html                  HTML shell (Google Fonts)
├── app.css                   All app styles (CSS vars for theme/font/accent/widths)
├── lib/
│   ├── data.js               Seed data + types (project, codebook, transcript, citations)
│   ├── state.svelte.js       Reactive app state (runes-based). Imported anywhere.
│   ├── api.js                Client → /api/* helpers (incl. SSE chat stream)
│   ├── Icon.svelte           Single icon component (name="search" etc.)
│   └── components/
│       ├── TopBar.svelte
│       ├── ContextPane.svelte
│       ├── FileRow.svelte
│       ├── TranscriptPane.svelte
│       ├── Waveform.svelte
│       ├── QuickCodeMenu.svelte
│       ├── CodebookPane.svelte
│       ├── ChatPane.svelte
│       ├── Message.svelte
│       ├── Citation.svelte
│       ├── SourcesUsed.svelte
│       ├── Assistant1.svelte (canned demo response)
│       ├── Assistant2.svelte (canned streaming demo)
│       └── Tweaks.svelte     (theme/font/accent/widths panel; persists to localStorage)
└── routes/
    ├── +layout.svelte
    ├── +page.svelte          The four-pane composition
    └── api/
        ├── chat/+server.js          ← SSE proxy → FastAPI /chat
        ├── files/+server.js         ← list + upload proxy
        ├── transcribe/+server.js    ← ASR kickoff proxy
        └── codebook/
            ├── +server.js           ← GET list + POST suggest
            └── [id]/+server.js      ← PATCH + DELETE
```

## State

Everything reactive lives in `src/lib/state.svelte.js` as a single `app`
object. Components import it and read/write fields directly — Svelte 5 runes
generate the getters/setters and propagate updates.

```js
import { app } from '$lib/state.svelte.js';

app.activeFile          // current file id
app.codebook            // hierarchical codes
app.tweaks              // user preferences (persisted to localStorage)
app.cite(7)             // jump to / flash citation #7
app.setTweak('dark', true)
```

If the codebase grows, split this file into per-domain stores (`files.svelte.js`,
`chat.svelte.js`, etc.) — keep the same rune-object pattern.

## Citations

Citations are first-class. `app.cites` is a registry keyed by integer ID:

```js
{
  1: { kind: 't', codeId: 'c14', turnTs: '00:00:24' },
  6: { kind: 'd', file: 'Prior coding — phase 1.pdf', fileId: 'f13',
       page: 12, score: 0.847, preview: '…' },
  …
}
```

The chat references citations by ID. Each `<Citation id={n} />` renders a chip
that, on click, calls `app.cite(n)` — which either scrolls the transcript to
the matching anchor (`kind: 't'`) or selects the source file in the context
sidebar (`kind: 'd'`).

When wiring up your FastAPI chat, return a `citations` array alongside the
streamed tokens (one entry per chunk retrieved from Chroma + one per transcript
match). The frontend's job is just to render the chips with the IDs the
server hands it.

## FastAPI contract (suggested)

| Route | Method | Returns |
|---|---|---|
| `/files` | GET | `Array<{id, name, type, status, meta, progress?}>` |
| `/files` | POST (multipart) | `{id, …}` after kicking off processing |
| `/transcribe` | POST `{fileId}` | `{jobId}` |
| `/chat` | POST `{messages, model, rag: {on, scope}}` | `text/event-stream` |
| `/codebook` | GET | `Array<{id, name, color, count, open, children: [...]}>` |
| `/codebook/suggest` | POST `{transcript, existing}` | `Array<{name, desc, parentId}>` |
| `/codebook/:id` | PATCH | `{ok: true}` |

### Chat SSE event format

Each `data:` line is JSON:

```
data: {"type":"token","value":"Three"}
data: {"type":"token","value":" patterns"}
data: {"type":"cite","value":{"id":4,"kind":"t","codeId":"c23","turnTs":"00:01:46"}}
data: {"type":"cite","value":{"id":6,"kind":"d","file":"…","page":12,"score":0.85,"preview":"…"}}
data: {"type":"done"}
```

`api.js` already parses this format in `streamChat()`.

## Styling

All design tokens are CSS custom properties at the top of `app.css`:

- `--bg, --bg-elev, --bg-sunk, --ink, --ink-2..4, --hair, --hair-2` — paper palette
- `--accent` — single accent color, set inline by the Tweaks panel
- `--code-1..6` — HSL triplets for the six code-highlight colors
- `--w-context, --w-codebook, --w-chat` — pane widths
- `--f-serif, --f-sans, --f-mono` — type stacks, switched via `data-font="…"`

Theme variants live under `html[data-theme="dark"]`.

## Notes

- `Tweaks.svelte` persists to `localStorage.qualscope.tweaks.v1`. Wipe to reset.
- `Assistant1.svelte` and `Assistant2.svelte` are *canned demo content* showing
  the chat surface. Replace them with a real `<MessageStream>` component that
  consumes `streamChat()` from `lib/api.js` when you wire to your backend.
- `Waveform.svelte` renders a deterministic pseudo-waveform. Swap with peaks
  from your backend's audio analysis (or web-audio decoding) when ready.
- Component split is "container vs. presentation"-flavoured: panes orchestrate,
  small components render. Keep it that way as you add features.
