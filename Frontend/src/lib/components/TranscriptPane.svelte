<script>
  import Icon from '$lib/Icon.svelte';
  import Waveform from './Waveform.svelte';
  import { app, codeColor, codeName, codebookWithCounts, fmtTime } from '$lib/state.svelte.js';
  import { getTranscript, updateTranscript, saveCodebook, setActiveCodebook } from '$lib/api.js';

  let playing = $state(false);
  let progress = $state(0);
  let transcript = $state(/** @type {any[]} */ ([]));
  let loading = $state(false);
  let noTranscript = $state(false);
  /** @type {HTMLAudioElement | null} */
  let audioEl = $state(null);

  let editing = $state(false);
  let saving = $state(false);
  /** @type {{ id: string, speaker: string, spk: string, ts: string, text: string }[]} */
  let editDraft = $state([]);

  /** @type {string | null} */
  let dragOverTurnId = $state(null);

  let activeFile = $derived(app.files.find((f) => f.id === app.activeFile));

  function parseDuration(meta) {
    const m = (meta ?? '').match(/^(\d+):(\d{2})(?::(\d{2}))?/);
    if (!m) return 0;
    if (m[3] !== undefined) return parseInt(m[1]) * 3600 + parseInt(m[2]) * 60 + parseInt(m[3]);
    return parseInt(m[1]) * 60 + parseInt(m[2]);
  }

  let totalSecs = $derived(parseDuration(activeFile?.meta));
  let isAudio = $derived(activeFile?.type === 'mp3');
  let isPdf = $derived(activeFile?.type === 'pdf');
  let audioSrc = $derived(isAudio && app.activeFile ? `/api/files/${app.activeFile}/audio` : null);
  let pdfSrc = $derived(isPdf && app.activeFile ? `/api/files/${app.activeFile}/pdf` : null);
  let title = $derived(activeFile?.name?.replace(/\.[^.]+$/, '') ?? 'Select a file');

  // Migrate legacy seg.code (single string) → turn.codes (array) on load.
  function normalizeTurn(turn) {
    if (turn.codes !== undefined) return turn;
    const legacyCodes = [...new Set(turn.segments.map((s) => s.code).filter(Boolean))];
    return {
      ...turn,
      codes: legacyCodes,
      segments: turn.segments.map(({ code, ...rest }) => rest)
    };
  }

  function findCodeInActiveCodebook(codeId) {
    for (const g of app.codebook) for (const c of g.children) if (c.id === codeId) return true;
    return false;
  }

  async function jumpToCodeOrigin(codeId) {
    const originId = findCodeInActiveCodebook(codeId)
      ? app.activeCodebookId
      : app.codeRegistry[codeId]?.codebookId;
    if (!originId || originId === app.activeCodebookId) return;
    try {
      const { activeId, codebook } = await setActiveCodebook(originId);
      app.activeCodebookId = activeId;
      app.codebook = codebook;
    } catch (e) {
      app.toast(`Could not switch to source codebook: ${e.message}`);
    }
  }

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
    const _v = app.transcriptVersion;
    if (!fid) return;
    transcript = [];
    noTranscript = false;
    loading = true;
    progress = 0;
    playing = false;

    getTranscript(fid)
      .then((turns) => {
        transcript = turns.map(normalizeTurn);
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
    const _t = transcript;
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

  function updateCodeCounts(updatedTranscript) {
    const updatedBook = codebookWithCounts(app.codebook, updatedTranscript);
    app.codebook = updatedBook;
    saveCodebook(updatedBook).catch((e) => app.toast(`Codebook save failed: ${e.message}`));
  }

  function applyCodeToTurn(turnId, codeId) {
    if (!app.activeFile) return;
    const updated = transcript.map((turn) => {
      if (turn.id !== turnId) return turn;
      if ((turn.codes ?? []).includes(codeId)) return turn;
      return { ...turn, codes: [...(turn.codes ?? []), codeId] };
    });
    transcript = updated;
    updateTranscript(app.activeFile, updated).catch((e) => app.toast(`Save failed: ${e.message}`));
    updateCodeCounts(updated);
  }

  function removeCodeFromTurn(turnId, codeId) {
    if (!app.activeFile) return;
    const updated = transcript.map((turn) => {
      if (turn.id !== turnId) return turn;
      return { ...turn, codes: (turn.codes ?? []).filter((id) => id !== codeId) };
    });
    transcript = updated;
    updateTranscript(app.activeFile, updated).catch((e) => app.toast(`Save failed: ${e.message}`));
    updateCodeCounts(updated);
  }

  function onDragOver(e, turnId) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    dragOverTurnId = turnId;
  }

  function onDragLeave(e, turnId) {
    if (dragOverTurnId === turnId) dragOverTurnId = null;
  }

  function onDrop(e, turnId) {
    e.preventDefault();
    dragOverTurnId = null;
    const codeId = e.dataTransfer.getData('application/x-qualscope-code');
    if (codeId) applyCodeToTurn(turnId, codeId);
  }

  function startEdit() {
    editDraft = transcript.map((turn) => ({
      id: turn.id,
      speaker: turn.speaker,
      spk: turn.spk,
      ts: turn.ts,
      text: turn.segments.map((s) => s.t).join(' '),
    }));
    editing = true;
  }

  function cancelEdit() {
    editing = false;
    editDraft = [];
  }

  function autoresize(node) {
    function resize() {
      node.style.height = 'auto';
      node.style.height = node.scrollHeight + 'px';
    }
    requestAnimationFrame(resize);
    node.addEventListener('input', resize);
    return { destroy() { node.removeEventListener('input', resize); } };
  }

  async function saveEdit() {
    if (!app.activeFile) return;
    saving = true;
    const savedTurns = editDraft.map((d) => {
      const orig = transcript.find((t) => t.id === d.id) ?? {};
      return { ...orig, id: d.id, speaker: d.speaker, spk: d.spk, ts: d.ts, segments: [{ t: d.text }] };
    });
    try {
      await updateTranscript(app.activeFile, savedTurns);
      transcript = savedTurns;
      editing = false;
      editDraft = [];
    } catch (e) {
      app.toast(`Save failed: ${e.message}`);
    } finally {
      saving = false;
    }
  }
</script>

<div class="pane">
  <div class="tr-head">
    <div class="tr-title-row">
      <h1 class="tr-title">{title}</h1>
      <div class="tr-meta">
        {#if activeFile}
          <span><span class="k">file</span> {activeFile.meta}</span>
          <span><span class="k">codes</span> {transcript.reduce((n, t) => n + (t.codes?.length ?? 0), 0)}</span>
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
      </div>
      <div class="grp">
        {#if editing}
          <button class="chip on" onclick={saveEdit} disabled={saving}>{saving ? 'saving…' : 'save'}</button>
          <button class="chip" onclick={cancelEdit} disabled={saving}>cancel</button>
        {:else}
          <button class="chip" onclick={startEdit} disabled={loading || noTranscript}>edit</button>
        {/if}
      </div>
    </div>
  </div>

  <div class="pane-body" style={isPdf && pdfSrc ? 'overflow:hidden; padding:0;' : ''}>
    {#if loading}
      <div style="padding:32px; text-align:center; color:var(--ink-4); font-family:var(--f-mono); font-size:11px;">
        loading…
      </div>
    {:else if noTranscript}
      {#if isPdf && pdfSrc}
        <iframe
          src={pdfSrc}
          title={activeFile?.name ?? 'PDF'}
          style="width:100%; height:100%; border:none; display:block;"
        ></iframe>
      {:else if isAudio}
        <div style="padding:32px; text-align:center; color:var(--ink-4); font-family:var(--f-mono); font-size:11px;">
          No transcript yet — right-click the file to transcribe.
        </div>
      {:else}
        <div style="padding:32px; text-align:center; color:var(--ink-4); font-family:var(--f-mono); font-size:11px;">
          Document indexed for RAG — no transcript view.
        </div>
      {/if}
    {:else if editing}
      <div class="tr-body">
        {#each editDraft as draft, i (draft.id)}
          <div class="tr-turn {draft.spk}">
            <div class="meta">
              <input
                bind:value={editDraft[i].speaker}
                style="font-size:11px;font-weight:600;font-family:var(--f-mono);border:1px solid var(--ink-3);border-radius:3px;padding:1px 5px;background:var(--bg-1);color:inherit;width:90px;"
              />
              <span class="ts">{draft.ts}</span>
            </div>
            <div class="tr-text">
              <textarea
                use:autoresize
                bind:value={editDraft[i].text}
                style="width:100%;font-size:13px;line-height:1.55;font-family:inherit;border:1px solid var(--ink-3);border-radius:4px;padding:5px 8px;background:var(--bg-1);color:inherit;resize:none;overflow:hidden;box-sizing:border-box;"
              ></textarea>
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <div class="tr-body">
        {#each transcript as turn (turn.id)}
          <!-- svelte-ignore a11y_no_static_element_interactions -->
          <div
            class="tr-turn {turn.spk}"
            class:drop-target={dragOverTurnId === turn.id}
            data-turn-id={turn.id}
            ondragover={(e) => onDragOver(e, turn.id)}
            ondragleave={(e) => onDragLeave(e, turn.id)}
            ondrop={(e) => onDrop(e, turn.id)}
          >
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
            <div class="tr-text">
              <p>
                {#each turn.segments as seg, si}
                  <span data-seg-idx={si}>{seg.t}{#if seg.cid}<span
                    class="cite-anchor"
                    class:flash={app.citeFlash === seg.cid}
                    data-cite={seg.cid}
                  >[{seg.cid}]</span>{/if}</span>
                {/each}
              </p>
              {#if turn.codes?.length}
                <div class="turn-codes">
                  {#each turn.codes as codeId}
                    {@const color = codeColor(app.codebook, codeId, app.codeRegistry)}
                    {@const isActive = app.activeCode === codeId}
                    <span
                      class="turn-code-badge c{color}"
                      class:active={isActive}
                      onmouseenter={() => (app.activeCode = codeId)}
                      onmouseleave={() => { if (app.activeCode === codeId) app.activeCode = null; }}
                      onclick={() => jumpToCodeOrigin(codeId)}
                      title="Switch to this code's codebook"
                      role="mark"
                    >
                      <span class="badge-dot"></span>
                      {codeName(app.codebook, codeId, app.codeRegistry)}
                      <button
                        class="badge-remove"
                        onclick={(e) => { e.stopPropagation(); removeCodeFromTurn(turn.id, codeId); }}
                        title="Remove code"
                      >✕</button>
                    </span>
                  {/each}
                </div>
              {/if}
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

  <audio
    bind:this={audioEl}
    src={audioSrc}
    ontimeupdate={onTimeUpdate}
    onended={onEnded}
    style="display:none;"
  ></audio>
</div>
