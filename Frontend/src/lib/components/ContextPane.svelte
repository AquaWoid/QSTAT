<script>
  import { onMount } from 'svelte';
  import Icon from '$lib/Icon.svelte';
  import FileRow from './FileRow.svelte';
  import { app } from '$lib/state.svelte.js';
  import { listFiles, uploadFile, deleteFile, fetchModels, fetchConfig, patchConfig } from '$lib/api.js';

  let audio = $derived(app.files.filter((f) => f.type === 'mp3'));
  let docs  = $derived(app.files.filter((f) => f.type !== 'mp3'));
  let dragging = $state(false);

  let settingsOpen = $state(false);
  let transcriptionModels = $state([]);
  let transcriptionModel = $state('faster-whisper');
  let rqHighlighted = $state(false);
  let rqInputEl = /** @type {HTMLTextAreaElement|null} */ (null);
  let _rqSaveTimer = null;

  $effect(() => {
    if (app.highlightRQ) {
      settingsOpen = true;
      rqHighlighted = true;
      app.highlightRQ = false;
      setTimeout(() => rqInputEl?.focus(), 50);
      setTimeout(() => { rqHighlighted = false; }, 1600);
    }
  });

  // Poll while any file is still processing
  let pollTimer = /** @type {ReturnType<typeof setInterval>|null} */ (null);

  function startPoll() {
    if (pollTimer) return;
    pollTimer = setInterval(async () => {
      const hasProc = app.files.some((f) => f.status === 'proc');
      if (!hasProc) {
        clearInterval(pollTimer);
        pollTimer = null;
        return;
      }
      try {
        app.files = await listFiles();
      } catch { /* ignore */ }
    }, 3000);
  }

  onMount(async () => {
    try {
      const files = await listFiles();
      if (files.length > 0) {
        app.files = files;
        if (!files.find((f) => f.id === app.activeFile)) {
          app.activeFile = files[0].id;
        }
      }
    } catch (e) {
      app.toast(`Could not load files: ${e.message}`);
    }
    if (app.files.some((f) => f.status === 'proc')) startPoll();

    try {
      const [models, cfg] = await Promise.all([fetchModels(), fetchConfig()]);
      transcriptionModels = models.transcription ?? [];
      transcriptionModel = cfg.transcription_model ?? 'faster-whisper';
      app.researchQuestion = cfg.researchContext?.rq ?? '';
    } catch { /* non-fatal */ }

    return () => { if (pollTimer) clearInterval(pollTimer); };
  });

  async function onTranscriptionModelChange(e) {
    transcriptionModel = e.target.value;
    try {
      await patchConfig({ transcription_model: transcriptionModel });
    } catch (e) {
      app.toast(`Config save failed: ${e.message}`);
    }
  }

  function onRQInput(e) {
    app.researchQuestion = e.target.value;
    clearTimeout(_rqSaveTimer);
    _rqSaveTimer = setTimeout(async () => {
      try {
        await patchConfig({ researchContext: { rq: app.researchQuestion } });
      } catch (err) {
        app.toast(`Config save failed: ${err.message}`);
      }
    }, 600);
  }

  async function handleFiles(fileList) {
    for (const file of fileList) {
      try {
        const meta = await uploadFile(file);
        // Optimistically prepend; poll will keep it updated
        app.files = [meta, ...app.files.filter((f) => f.id !== meta.id)];
        startPoll();
      } catch (e) {
        app.toast(`Upload failed: ${e.message}`);
      }
    }
  }

  async function handleDelete(id) {
    try {
      await deleteFile(id);
      app.files = app.files.filter((f) => f.id !== id);
      if (app.activeFile === id) {
        app.activeFile = app.files[0]?.id ?? null;
      }
    } catch (e) {
      app.toast(`Delete failed: ${e.message}`);
    }
  }

  function onDrop(e) {
    e.preventDefault();
    dragging = false;
    if (e.dataTransfer?.files?.length) handleFiles(e.dataTransfer.files);
  }

  function onDragOver(e) { e.preventDefault(); dragging = true; }
  function onDragLeave()  { dragging = false; }

  function onClickUpload() {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    input.accept = '.mp3,.mp4,.pdf,.docx,.doc,.xlsx,.xls';
    input.onchange = () => { if (input.files?.length) handleFiles(input.files); };
    input.click();
  }
</script>

<div class="pane elev" style="border-right:none;">
  <div class="pane-hd">
    <span class="lbl">Project Context</span>
    <div class="actions">
      <button class="iconbtn" class:active={settingsOpen} title="Settings" onclick={() => (settingsOpen = !settingsOpen)}>
        <Icon name="settings" />
      </button>
    </div>
  </div>

  <div class="pane-body">
    {#if settingsOpen}
      <div class="ctx-settings">
        <div class="ctx-settings-row">
          <label for="transcription-model">Transcription model</label>
          <select id="transcription-model" value={transcriptionModel} onchange={onTranscriptionModelChange}>
            {#each transcriptionModels as m}
              <option value={m.identifier}>{m.name}</option>
            {/each}
          </select>
        </div>
        <div class="ctx-settings-row col">
          <label for="research-question">Research question</label>
          <textarea
            id="research-question"
            bind:this={rqInputEl}
            class:highlight={rqHighlighted}
            value={app.researchQuestion}
            oninput={onRQInput}
            placeholder="What is your research question?"
            rows="3"
          ></textarea>
        </div>
      </div>
    {/if}

    <div class="ctx-section">
      <span>Audio · {audio.length}</span>
      <span class="count">{audio.filter((a) => a.status === 'ok').length} ready</span>
    </div>
    <div class="ctx-list">
      {#each audio as f (f.id)}
        <FileRow {f} active={f.id === app.activeFile} onpick={(id) => (app.activeFile = id)} ondelete={handleDelete} />
      {/each}
    </div>

    <div class="ctx-section">
      <span>Documents · {docs.length}</span>
    </div>
    <div class="ctx-list">
      {#each docs as f (f.id)}
        <FileRow {f} active={f.id === app.activeFile} onpick={(id) => (app.activeFile = id)} ondelete={handleDelete} />
      {/each}
    </div>

    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="ctx-upload"
      class:dragging
      ondrop={onDrop}
      ondragover={onDragOver}
      ondragleave={onDragLeave}
      onclick={onClickUpload}
      role="button"
      tabindex="0"
      onkeydown={(e) => e.key === 'Enter' && onClickUpload()}
    >
      drop files here<br />
      <span style="color: var(--ink-3);">or click to upload</span>
    </div>
  </div>

  <div class="ctx-foot">
    <div class="avatar">LW</div>
    <div style="display:flex; flex-direction:column;">
      <span style="color: var(--ink-2);">Example User</span>
      <span>last sync · 14:02</span>
    </div>
  </div>
</div>

<style>
  .ctx-upload.dragging {
    border-color: var(--accent);
    background: color-mix(in oklch, var(--accent) 8%, var(--bg-sunk));
  }

  .iconbtn.active { color: var(--ink); background: var(--bg-sunk); }

  .ctx-settings {
    padding: 8px 10px 10px;
    border-bottom: 1px solid var(--hair-2);
  }

  .ctx-settings-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
  }

  .ctx-settings-row label {
    font-size: 11px;
    color: var(--ink-2);
    white-space: nowrap;
  }

  .ctx-settings-row.col {
    flex-direction: column;
    align-items: stretch;
    gap: 4px;
    margin-top: 8px;
  }

  .ctx-settings-row select {
    flex: 1;
    min-width: 0;
    font-size: 11px;
    font-family: inherit;
    color: var(--ink);
    background: var(--bg-sunk);
    border: 1px solid var(--hair-2);
    border-radius: 4px;
    padding: 3px 6px;
    cursor: pointer;
    outline: none;
  }

  .ctx-settings-row select:focus {
    border-color: var(--accent);
  }

  .ctx-settings-row textarea {
    font-size: 11px;
    font-family: inherit;
    color: var(--ink);
    background: var(--bg-sunk);
    border: 1px solid var(--hair-2);
    border-radius: 4px;
    padding: 4px 6px;
    resize: vertical;
    outline: none;
    line-height: 1.5;
  }

  .ctx-settings-row textarea:focus {
    border-color: var(--accent);
  }

  .ctx-settings-row textarea.highlight {
    border-color: var(--accent);
    animation: rq-flash 1.6s ease-out forwards;
  }

  @keyframes rq-flash {
    0%   { box-shadow: 0 0 0 2px color-mix(in oklch, var(--accent) 40%, transparent); }
    60%  { box-shadow: 0 0 0 2px color-mix(in oklch, var(--accent) 40%, transparent); }
    100% { box-shadow: none; border-color: var(--hair-2); }
  }
</style>
