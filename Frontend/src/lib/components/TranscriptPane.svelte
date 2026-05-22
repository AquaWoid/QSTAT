<script>
  import Icon from '$lib/Icon.svelte';
  import Waveform from './Waveform.svelte';
  import QuickCodeMenu from './QuickCodeMenu.svelte';
  import { app, codeColor, fmtTime } from '$lib/state.svelte.js';
  import { getTranscript, updateTranscript } from '$lib/api.js';

  let playing = $state(false);
  let progress = $state(0);
  let transcript = $state(/** @type {any[]} */ ([]));
  let loading = $state(false);
  let noTranscript = $state(false);
  /** @type {HTMLAudioElement | null} */
  let audioEl = $state(null);

  /** @type {{ x: number, y: number } | null} */
  let qcode = $state(null);
  /** @type {{ turnId: string, segStart: number, segEnd: number } | null} */
  let currentSelection = $state(null);

  let activeFile = $derived(app.files.find((f) => f.id === app.activeFile));

  function parseDuration(meta) {
    const m = (meta ?? '').match(/^(\d+):(\d{2})(?::(\d{2}))?/);
    if (!m) return 0;
    if (m[3] !== undefined) return parseInt(m[1]) * 3600 + parseInt(m[2]) * 60 + parseInt(m[3]);
    return parseInt(m[1]) * 60 + parseInt(m[2]);
  }

  let totalSecs = $derived(parseDuration(activeFile?.meta));
  let isAudio = $derived(activeFile?.type === 'mp3');
  let audioSrc = $derived(isAudio && app.activeFile ? `/api/files/${app.activeFile}/audio` : null);
  let title = $derived(activeFile?.name?.replace(/\.[^.]+$/, '') ?? 'Select a file');

  function seekToTs(ts) {
    const parts = ts.split(':').map(Number);
    const secs = parts.length === 3
      ? parts[0] * 3600 + parts[1] * 60 + parts[2]
      : parts[0] * 60 + parts[1];
    if (audioEl && audioEl.duration) {
      audioEl.currentTime = secs;
    } else if (totalSecs) {
      progress = secs / totalSecs;
    }
  }

  function onWaveClick(e) {
    const rect = /** @type {HTMLElement} */ (e.currentTarget).getBoundingClientRect();
    const frac = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    if (audioEl && audioEl.duration) {
      audioEl.currentTime = frac * audioEl.duration;
    } else {
      progress = frac;
    }
  }

  // Fetch transcript on file change
  $effect(() => {
    const fid = app.activeFile;
    if (!fid) return;
    transcript = [];
    noTranscript = false;
    loading = true;
    progress = 0;
    playing = false;

    getTranscript(fid)
      .then((turns) => {
        transcript = turns;
        noTranscript = turns.length === 0;
      })
      .catch(() => { noTranscript = true; })
      .finally(() => { loading = false; });
  });

  // Play/pause real audio
  $effect(() => {
    if (!audioEl) return;
    if (playing) audioEl.play().catch(() => { playing = false; });
    else audioEl.pause();
  });

  // Scroll to a cited turn when requested by app.cite()
  $effect(() => {
    const turnId = app.pendingTurnScroll;
    const _t = transcript; // reactive dependency — re-runs after transcript loads
    if (!turnId || loading) return;
    queueMicrotask(() => {
      const el = document.querySelector(`[data-turn-id="${turnId}"]`);
      if (el) {
        const container = el.closest('.pane-body');
        if (container) {
          const rect = el.getBoundingClientRect();
          const cRect = container.getBoundingClientRect();
          container.scrollTop += rect.top - cRect.top - 80;
        }
      }
      app.pendingTurnScroll = null;
    });
  });

  function onTimeUpdate() {
    if (audioEl && audioEl.duration) progress = audioEl.currentTime / audioEl.duration;
  }

  function onEnded() { playing = false; }

  function onSelect() {
    const sel = window.getSelection?.();
    if (!sel || sel.isCollapsed) { qcode = null; return; }

    const range = sel.getRangeAt(0);
    const startEl = range.startContainer.nodeType === 3
      ? range.startContainer.parentElement
      : /** @type {Element} */ (range.startContainer);
    const endEl = range.endContainer.nodeType === 3
      ? range.endContainer.parentElement
      : /** @type {Element} */ (range.endContainer);

    const turnEl = startEl?.closest?.('[data-turn-id]');
    if (!turnEl) { qcode = null; return; }

    const turnId = turnEl.getAttribute('data-turn-id') ?? '';
    const segStart = parseInt(startEl?.closest?.('[data-seg-idx]')?.getAttribute('data-seg-idx') ?? '0');
    const segEnd = parseInt(endEl?.closest?.('[data-seg-idx]')?.getAttribute('data-seg-idx') ?? String(segStart));

    currentSelection = { turnId, segStart, segEnd: Math.max(segStart, segEnd) };

    const rect = range.getBoundingClientRect();
    if (rect.width > 4) qcode = { x: rect.left + rect.width / 2, y: rect.bottom + 8 };
  }

  function applyCode(codeId) {
    if (!currentSelection || !app.activeFile) { closeQcode(); return; }
    const { turnId, segStart, segEnd } = currentSelection;

    const updated = transcript.map((turn) => {
      if (turn.id !== turnId) return turn;
      return {
        ...turn,
        segments: turn.segments.map((seg, i) =>
          i >= segStart && i <= segEnd ? { ...seg, code: codeId } : seg
        )
      };
    });

    transcript = updated;
    updateTranscript(app.activeFile, updated).catch((e) => app.toast(`Save failed: ${e.message}`));
    closeQcode();
  }

  function newCodeFromSelection() {
    const name = prompt('New code name:');
    if (!name?.trim()) { closeQcode(); return; }
    const group = app.codebook[0];
    if (!group) { app.toast('Create a code group first.'); closeQcode(); return; }
    const newCode = { id: `c_${Date.now()}`, name: name.trim(), color: group.color, count: 0, desc: '' };
    app.codebook = app.codebook.map((g) =>
      g.id === group.id ? { ...g, children: [...g.children, newCode] } : g
    );
    applyCode(newCode.id);
  }

  function handleSuggest() {
    closeQcode();
    app.toast('Use "Suggest codes" in the Codebook pane.', 'info');
  }

  function closeQcode() {
    qcode = null;
    currentSelection = null;
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
          <span><span class="k">turns</span> {transcript.length}</span>
        {/if}
      </div>
    </div>

    {#if isAudio}
      <div class="player">
        <button class="play" onclick={() => (playing = !playing)}>
          <Icon name={playing ? 'pause' : 'play'} />
        </button>
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div class="wave" style="color: var(--ink-3); cursor:pointer;" onclick={onWaveClick}>
          <Waveform {progress} />
        </div>
        <div class="time">
          <span class="cur">{fmtTime(progress * totalSecs)}</span>
          <span class="sep">/</span>
          <span>{activeFile?.meta?.split(' ·')[0] ?? '—'}</span>
        </div>
      </div>
    {/if}

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
    </div>
  </div>

  <div class="pane-body">
    {#if loading}
      <div style="padding:32px; text-align:center; color:var(--ink-4); font-family:var(--f-mono); font-size:11px;">
        loading…
      </div>
    {:else if noTranscript}
      <div style="padding:32px; text-align:center; color:var(--ink-4); font-family:var(--f-mono); font-size:11px;">
        {#if isAudio}
          No transcript yet — right-click the file to transcribe.
        {:else}
          Document indexed for RAG — no transcript view.
        {/if}
      </div>
    {:else}
      <div class="tr-body">
        {#each transcript as turn (turn.id)}
          <div class="tr-turn {turn.spk}" data-turn-id={turn.id}>
            <div class="meta">
              <span class="spk">{turn.speaker}</span>
              <!-- svelte-ignore a11y_no_static_element_interactions -->
              <span
                class="ts"
                title="click to seek"
                onclick={() => seekToTs(turn.ts)}
                style="cursor:pointer;"
              >{turn.ts}</span>
            </div>
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div class="tr-text" onmouseup={onSelect}>
              <p>
                {#each turn.segments as seg, si}
                  {#if seg.code}
                    {@const isActive = app.activeCode === seg.code}
                    <span
                      class="code c{codeColor(app.codebook, seg.code)}"
                      class:active={isActive}
                      data-seg-idx={si}
                      onmouseenter={() => (app.activeCode = seg.code)}
                      onmouseleave={() => (app.activeCode = null)}
                      role="mark"
                    >{seg.t}{#if seg.cid}<span
                        class="cite-anchor"
                        class:flash={app.citeFlash === seg.cid}
                        data-cite={seg.cid}
                      >[{seg.cid}]</span>{/if}</span>
                  {:else}
                    <span data-seg-idx={si}>{seg.t}</span>
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
    <QuickCodeMenu
      codebook={app.codebook}
      pos={qcode}
      onclose={closeQcode}
      onapply={applyCode}
      onnewcode={newCodeFromSelection}
      onsuggest={handleSuggest}
    />
  {/if}

  <audio
    bind:this={audioEl}
    src={audioSrc}
    ontimeupdate={onTimeUpdate}
    onended={onEnded}
    style="display:none;"
  ></audio>
</div>
