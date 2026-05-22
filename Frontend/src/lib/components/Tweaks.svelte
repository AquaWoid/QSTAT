<script>
  import { app, ACCENTS_LIGHT, ACCENTS_DARK } from '$lib/state.svelte.js';

  let open = $state(false);

  let t = $derived(app.tweaks);

  function set(key, value) {
    app.setTweak(key, value);
  }

  // When dark mode flips, swap accent to the matching theme sibling
  $effect(() => {
    const li = ACCENTS_LIGHT.indexOf(t.accent);
    const di = ACCENTS_DARK.indexOf(t.accent);
    if (t.dark && li !== -1) set('accent', ACCENTS_DARK[li]);
    if (!t.dark && di !== -1) set('accent', ACCENTS_LIGHT[di]);
  });

  // Apply tweaks to <html>
  $effect(() => {
    const html = document.documentElement;
    html.setAttribute('data-theme', t.dark ? 'dark' : 'light');
    html.setAttribute('data-font', t.font);
    html.style.setProperty('--accent', t.accent);
    html.style.setProperty('--w-context',  t.wContext  + 'px');
    html.style.setProperty('--w-codebook', t.wCodebook + 'px');
    html.style.setProperty('--w-chat',     t.wChat     + 'px');
    html.classList.toggle('no-context', !t.showContext);
    html.classList.toggle('no-chat',    !t.showChat);
  });

  let accents = $derived(t.dark ? ACCENTS_DARK : ACCENTS_LIGHT);
</script>

<button class="tweaks-fab" onclick={() => (open = !open)} title="Tweaks">
  <svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
    <circle cx="8" cy="8" r="2" />
    <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.4 1.4M11.6 11.6 13 13M3 13l1.4-1.4M11.6 4.4 13 3" />
  </svg>
</button>

{#if open}
  <div class="tweaks-panel">
    <div class="tweaks-hd">
      <b>Tweaks</b>
      <button class="x" onclick={() => (open = false)} aria-label="Close">×</button>
    </div>
    <div class="tweaks-body">
      <div class="sect">Theme</div>
      <label class="row">
        <span>Dark mode</span>
        <input type="checkbox" checked={t.dark} oninput={(e) => set('dark', e.currentTarget.checked)} />
      </label>
      <div class="row">
        <span>Accent</span>
        <div class="swatches">
          {#each accents as c}
            <button
              class="swatch"
              class:on={t.accent === c}
              style="background: {c};"
              onclick={() => set('accent', c)}
              aria-label="Accent {c}"
            ></button>
          {/each}
        </div>
      </div>

      <div class="sect">Typography</div>
      <div class="row col">
        <span>Font pairing</span>
        <select value={t.font} onchange={(e) => set('font', e.currentTarget.value)}>
          <option value="newsreader-plex">Newsreader / IBM Plex Sans</option>
          <option value="spectral-geist">Spectral / Geist</option>
          <option value="fraunces-publicsans">Source Serif / Public Sans</option>
        </select>
      </div>

      <div class="sect">Panel widths</div>
      <label class="row">
        <span>Context · <em>{t.wContext}px</em></span>
        <input type="range" min="180" max="320" value={t.wContext} oninput={(e) => set('wContext', +e.currentTarget.value)} />
      </label>
      <label class="row">
        <span>Codebook · <em>{t.wCodebook}px</em></span>
        <input type="range" min="220" max="380" value={t.wCodebook} oninput={(e) => set('wCodebook', +e.currentTarget.value)} />
      </label>
      <label class="row">
        <span>Chat · <em>{t.wChat}px</em></span>
        <input type="range" min="280" max="460" value={t.wChat} oninput={(e) => set('wChat', +e.currentTarget.value)} />
      </label>

      <div class="sect">Show</div>
      <label class="row">
        <span>Project Context</span>
        <input type="checkbox" checked={t.showContext} oninput={(e) => set('showContext', e.currentTarget.checked)} />
      </label>
      <label class="row">
        <span>Chat</span>
        <input type="checkbox" checked={t.showChat} oninput={(e) => set('showChat', e.currentTarget.checked)} />
      </label>
    </div>
  </div>
{/if}

<style>
  .tweaks-fab {
    position: fixed; right: 16px; bottom: 16px;
    z-index: 90;
    width: 32px; height: 32px;
    border-radius: 50%;
    background: var(--bg-elev);
    color: var(--ink-3);
    border: 1px solid var(--hair);
    box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    display: grid; place-items: center;
    cursor: default;
  }
  .tweaks-fab:hover { color: var(--accent); border-color: var(--accent); }

  .tweaks-panel {
    position: fixed; right: 16px; bottom: 56px;
    z-index: 91;
    width: 280px; max-height: calc(100vh - 88px);
    display: flex; flex-direction: column;
    background: var(--bg-elev);
    color: var(--ink);
    border: 1px solid var(--hair);
    border-radius: 6px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    font-family: var(--f-sans); font-size: 12px;
    overflow: hidden;
  }
  .tweaks-hd {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 8px 10px 14px;
    border-bottom: 1px solid var(--hair);
  }
  .tweaks-hd b {
    font-family: var(--f-serif); font-style: italic; font-weight: 500; font-size: 14px;
  }
  .tweaks-hd .x {
    width: 22px; height: 22px; border-radius: 4px;
    background: none; border: 0; color: var(--ink-3); font-size: 16px; line-height: 1;
    cursor: default;
  }
  .tweaks-hd .x:hover { background: var(--bg-sunk); color: var(--ink); }

  .tweaks-body {
    padding: 6px 14px 14px;
    display: flex; flex-direction: column; gap: 8px;
    overflow-y: auto;
  }
  .sect {
    font-family: var(--f-mono); font-size: 9.5px;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--ink-4);
    margin: 10px 0 0;
  }
  .row {
    display: flex; align-items: center; justify-content: space-between;
    gap: 10px;
    color: var(--ink-2);
    font-size: 11.5px;
  }
  .row.col { flex-direction: column; align-items: stretch; gap: 4px; }
  .row em { font-style: normal; font-family: var(--f-mono); font-size: 10px; color: var(--ink-4); }
  .row input[type='range'] { width: 130px; }
  .row select {
    padding: 4px 6px;
    border: 1px solid var(--hair-2); border-radius: 3px;
    background: var(--bg); color: var(--ink);
    font-size: 11.5px;
  }

  .swatches { display: flex; gap: 4px; }
  .swatch {
    width: 22px; height: 22px;
    border-radius: 4px;
    border: 1px solid var(--hair-2);
    cursor: default;
  }
  .swatch.on { box-shadow: 0 0 0 2px var(--bg-elev), 0 0 0 3px currentColor; }
</style>
