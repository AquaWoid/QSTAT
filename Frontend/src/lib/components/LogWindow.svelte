<script>
  import { app } from '$lib/state.svelte.js';

  const MAX_LINES = 500;

  let logs = $state(/** @type {Array<{id:number, ts:number, level:string, message:string}>} */ ([]));
  let logSeq = 0;
  let bodyEl = $state(/** @type {HTMLElement | null} */ (null));
  let stick = true;

  // Only hold an SSE connection while the panel is actually open.
  $effect(() => {
    if (!app.logsOpen) return;

    const es = new EventSource('/api/logs');
    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data);
        logs = [...logs, { id: ++logSeq, ts: Date.now(), level: data.level ?? 'info', message: data.message }].slice(-MAX_LINES);
      } catch {
        // Ignore malformed events rather than breaking the stream.
      }
    };

    return () => es.close();
  });

  $effect(() => {
    logs.length; // track
    if (stick && bodyEl) {
      const el = bodyEl;
      queueMicrotask(() => { el.scrollTop = el.scrollHeight; });
    }
  });

  function onScroll() {
    if (!bodyEl) return;
    stick = bodyEl.scrollHeight - bodyEl.scrollTop - bodyEl.clientHeight < 24;
  }

  function clear() {
    logs = [];
  }

  function fmtTs(ts) {
    const d = new Date(ts);
    return d.toLocaleTimeString('en-GB', { hour12: false }) + '.' + String(d.getMilliseconds()).padStart(3, '0');
  }
</script>

{#if app.logsOpen}
  <div class="log-panel">
    <div class="log-hd">
      <b>Console</b>
      <div class="log-actions">
        <button class="lbtn" onclick={clear}>clear</button>
        <button class="x" onclick={() => (app.logsOpen = false)} aria-label="Close">×</button>
      </div>
    </div>
    <div class="log-body" bind:this={bodyEl} onscroll={onScroll}>
      {#if logs.length === 0}
        <div class="empty">No log output yet.</div>
      {:else}
        {#each logs as l (l.id)}
          <div class="line lvl-{l.level}">
            <span class="ts">{fmtTs(l.ts)}</span>
            <span class="lvl">{l.level}</span>
            <span class="msg">{l.message}</span>
          </div>
        {/each}
      {/if}
    </div>
  </div>
{/if}

<style>
  .log-panel {
    position: fixed; left: 8px; bottom: 8px;
    z-index: 91;
    width: 560px; height: 300px;
    display: flex; flex-direction: column;
    background: var(--bg-elev);
    color: var(--ink);
    border: 1px solid var(--hair);
    border-radius: 6px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    font-family: var(--f-sans); font-size: 12px;
    overflow: hidden;
  }
  .log-hd {
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 8px 8px 14px;
    border-bottom: 1px solid var(--hair);
  }
  .log-hd b {
    font-family: var(--f-serif); font-style: italic; font-weight: 500; font-size: 14px;
  }
  .log-actions { display: flex; align-items: center; gap: 4px; }
  .log-actions .lbtn {
    padding: 3px 8px;
    border-radius: 4px;
    background: none; border: 0; color: var(--ink-3);
    font-family: var(--f-mono); font-size: 10.5px;
    cursor: default;
  }
  .log-actions .lbtn:hover { background: var(--bg-sunk); color: var(--ink); }
  .log-actions .x {
    width: 22px; height: 22px; border-radius: 4px;
    background: none; border: 0; color: var(--ink-3); font-size: 16px; line-height: 1;
    cursor: default;
  }
  .log-actions .x:hover { background: var(--bg-sunk); color: var(--ink); }

  .log-body {
    flex: 1;
    padding: 6px 10px;
    overflow-y: auto;
    font-family: var(--f-mono); font-size: 11px; line-height: 1.6;
  }
  .empty { color: var(--ink-4); padding: 4px 4px; }

  .line { display: flex; gap: 8px; white-space: pre-wrap; word-break: break-word; }
  .line .ts { color: var(--ink-4); flex-shrink: 0; }
  .line .lvl { flex-shrink: 0; width: 4.5em; text-transform: uppercase; font-size: 9.5px; letter-spacing: 0.04em; }
  .line .msg { color: var(--ink-2); }

  .lvl-info .lvl { color: var(--ink-3); }
  .lvl-warn .lvl, .lvl-warning .lvl { color: oklch(0.65 0.15 80); }
  .lvl-error .lvl { color: oklch(0.55 0.18 25); }
  .lvl-error .msg { color: oklch(0.55 0.18 25); }
</style>
