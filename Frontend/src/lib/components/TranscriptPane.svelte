<script>
  import Icon from '$lib/Icon.svelte';
  import Waveform from './Waveform.svelte';
  import QuickCodeMenu from './QuickCodeMenu.svelte';
  import { app, codeColor, fmtTime } from '$lib/state.svelte.js';
  import { TRANSCRIPT } from '$lib/data.js';
  import { getTranscript } from '$lib/api.js';

  let playing = $state(false);
  let progress = $state(0.42);
  let transcript = $state(TRANSCRIPT);
  let loading = $state(false);

  /** @type {{ x: number, y: number } | null} */
  let qcode = $state(null);

  // Fetch transcript when active file changes
  $effect(() => {
    const fid = app.activeFile;
    if (!fid) return;
    loading = true;
    getTranscript(fid)
      .then((turns) => {
        transcript = turns;
        progress = 0;
        playing = false;
      })
      .catch(() => {
        // File has no transcript yet (might be a document or not-yet-transcribed audio)
        // Keep showing the current transcript rather than clearing to empty
      })
      .finally(() => { loading = false; });
  });

  // Demo: advance scrubber when "playing"
  $effect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      progress = Math.min(1, progress + 0.005);
    }, 100);
    return () => clearInterval(id);
  });

  let activeFile = $derived(app.files.find((f) => f.id === app.activeFile));
  let title = $derived(activeFile?.name?.replace(/\.[^.]+$/, '') ?? 'Select a file');

  function onSelect() {
    const sel = window.getSelection?.();
    if (!sel || sel.isCollapsed) { qcode = null; return; }
    const rect = sel.getRangeAt(0).getBoundingClientRect();
    if (rect.width > 4) {
      qcode = { x: rect.left + rect.width / 2, y: rect.bottom + 8 };
    }
  }

  function closeQcode() {
    qcode = null;
    window.getSelection?.()?.removeAllRanges();
  }
</script>

<div class="pane">
  <div class="tr-head">
    <div class="tr-title-row">
      <h1 class="tr-title">{title}</h1>
      <div class="tr-meta">
        {#if activeFile}
          <span><span class="k">file</span> {activeFile.meta}</span>
          <span><span class="k">codes</span> {transcript.reduce((n, t) => n + t.segments.filter((s) => s.code).length, 0)}</span>
        {/if}
      </div>
    </div>

    <div class="player">
      <button class="play" onclick={() => (playing = !playing)}>
        <Icon name={playing ? 'pause' : 'play'} />
      </button>
      <div class="wave" style="color: var(--ink-3);">
        <Waveform {progress} />
      </div>
      <div class="time">
        <span class="cur">{fmtTime(progress * 60 * 60)}</span>
        <span class="sep">/</span>
        <span>{activeFile?.meta?.split(' ·')[0] ?? '—'}</span>
      </div>
    </div>

    <div class="tr-toolbar">
      <div class="grp">
        <button class="chip on">codes</button>
        <button class="chip">timestamps</button>
        <button class="chip">confidence</button>
      </div>
      <div class="grp">
        <button class="chip">edit</button>
        <button class="chip">find</button>
      </div>
      <div class="speakers">
        <span class="sp a"><span class="swatch"></span>Interviewer</span>
        <span class="sp b"><span class="swatch"></span>Speaker</span>
      </div>
    </div>
  </div>

  <div class="pane-body">
    {#if loading}
      <div style="padding:24px; text-align:center; color:var(--ink-4); font-family:var(--f-mono); font-size:11px;">
        loading transcript…
      </div>
    {:else}
      <div class="tr-body">
        {#each transcript as turn (turn.id)}
          <div class="tr-turn {turn.spk}">
            <div class="meta">
              <span class="spk">{turn.speaker}</span>
              <span class="ts" title="click to seek">{turn.ts}</span>
            </div>
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div class="tr-text" onmouseup={onSelect}>
              <p>
                {#each turn.segments as seg}
                  {#if seg.code}
                    {@const isActive = app.activeCode === seg.code}
                    <span
                      class="code c{codeColor(app.codebook, seg.code)}"
                      class:active={isActive}
                      onmouseenter={() => (app.activeCode = seg.code)}
                      onmouseleave={() => (app.activeCode = null)}
                      role="mark"
                    >{seg.t}{#if seg.cid}<span
                        class="cite-anchor"
                        class:flash={app.citeFlash === seg.cid}
                        data-cite={seg.cid}
                      >[{seg.cid}]</span>{/if}</span>
                  {:else}
                    <span>{seg.t}</span>
                  {/if}
                {/each}
              </p>
            </div>
          </div>
        {/each}
        {#if transcript.length}
          <div style="text-align:center; color:var(--ink-4); font-family:var(--f-mono); font-size:10px; letter-spacing:0.1em; padding:20px 0 0; text-transform:uppercase;">
            ─── end of transcript ───
          </div>
        {/if}
      </div>
    {/if}
  </div>

  {#if qcode}
    <QuickCodeMenu codebook={app.codebook} pos={qcode} onclose={closeQcode} />
  {/if}
</div>
