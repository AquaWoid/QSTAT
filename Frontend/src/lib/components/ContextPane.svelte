<script>
  import { onMount } from 'svelte';
  import Icon from '$lib/Icon.svelte';
  import FileRow from './FileRow.svelte';
  import { app } from '$lib/state.svelte.js';
  import { listFiles, uploadFile, deleteFile } from '$lib/api.js';

  let audio = $derived(app.files.filter((f) => f.type === 'mp3'));
  let docs  = $derived(app.files.filter((f) => f.type !== 'mp3'));
  let dragging = $state(false);

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
    return () => { if (pollTimer) clearInterval(pollTimer); };
  });

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
      <!-- Might reimplement - Not sure yet if it's really neccesary
       <button class="iconbtn" title="Sort"><Icon name="sort" /></button>
      <button class="iconbtn" title="Filter"><Icon name="filter" /></button>         
      -->
    </div>
  </div>

  <div class="pane-body">
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
</style>
