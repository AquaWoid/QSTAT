<script>
  import { onMount } from 'svelte';
  import Icon from '$lib/Icon.svelte';
  import { app, codebookWithCounts, buildCodeRegistry } from '$lib/state.svelte.js';
  import {
    getCodebook, saveCodebook, generateCodebook, generateDeductiveCodebook, getTranscript,
    autoAnnotateTranscript,
    listCodebooks, setActiveCodebook, renameCodebook, deleteCodebook, mergeCodebooks, getCodebookById
  } from '$lib/api.js';

  let codebooks = $state(/** @type {Array<{id:string,name:string,createdAt:string}>} */ ([]));
  let cbMenuOpen = $state(false);
  let renamingCodebook = $state(false);

  let activeCodebookName = $derived(codebooks.find((c) => c.id === app.activeCodebookId)?.name ?? 'Codebook');

  async function refreshCodebookList() {
    try {
      const { items, activeId } = await listCodebooks();
      codebooks = items;
      app.activeCodebookId = activeId;
      app.codeRegistry = await buildCodeRegistry(items, getCodebookById);
    } catch (e) {
      app.toast(`Could not load codebooks: ${e.message}`);
    }
  }

  async function switchCodebook(id) {
    cbMenuOpen = false;
    if (id === app.activeCodebookId) return;
    try {
      const { activeId, codebook } = await setActiveCodebook(id);
      app.activeCodebookId = activeId;
      app.codebook = codebook;
    } catch (e) {
      app.toast(`Could not switch codebook: ${e.message}`);
    }
  }

  function startRenameCodebook(e) {
    cbMenuOpen = false;
    renamingCodebook = true;
    setTimeout(() => /** @type {HTMLElement} */ (e.target).focus(), 0);
  }

  async function finishRenameCodebook(newName) {
    renamingCodebook = false;
    const name = (newName || '').trim();
    const current = codebooks.find((c) => c.id === app.activeCodebookId);
    if (!name || !app.activeCodebookId || current?.name === name) return;
    try {
      await renameCodebook(app.activeCodebookId, name);
      codebooks = codebooks.map((c) => (c.id === app.activeCodebookId ? { ...c, name } : c));
    } catch (e) {
      app.toast(`Rename failed: ${e.message}`);
    }
  }

  async function handleDeleteCodebook(id, e) {
    e.stopPropagation();
    if (codebooks.length <= 1) { app.toast('Cannot delete the only codebook'); return; }
    if (!confirm('Delete this codebook?')) return;
    try {
      const { items, activeId, codebook } = await deleteCodebook(id);
      codebooks = items;
      app.activeCodebookId = activeId;
      app.codebook = codebook;
      app.codeRegistry = await buildCodeRegistry(items, getCodebookById);
    } catch (e2) {
      app.toast(`Delete failed: ${e2.message}`);
    }
  }

  let query = $state('');
  let editing = $state(/** @type {{id: string, field: 'name'|'desc'} | null} */ (null));
  let generating = $state(false);
  let deducting = $state(false);
  let annotating = $state(false);
  let expandedDescs = $state(/** @type {Set<string>} */ (new Set()));

  function toggleDesc(id) {
    const next = new Set(expandedDescs);
    if (next.has(id)) next.delete(id); else next.add(id);
    expandedDescs = next;
  }

  // Inline add-group form
  let addingGroup = $state(false);
  let newGroupName = $state('');
  let newGroupColor = $state('1');

  // Per-group "..." menu open state
  let menuOpenId = $state(/** @type {string | null} */ (null));

  // Debounce timer for text edits
  let _saveTimer = null;

  function persistNow(book) {
    clearTimeout(_saveTimer);
    saveCodebook(book).catch((e) => app.toast(`Failed to save codebook: ${e.message}`));
  }

  function persistDebounced(book) {
    clearTimeout(_saveTimer);
    _saveTimer = setTimeout(() => {
      saveCodebook(book).catch((e) => app.toast(`Failed to save codebook: ${e.message}`));
    }, 400);
  }

  const COLORS = ['1', '2', '3', '4', '5', '6'];

  function toggleGroup(gid) {
    app.codebook = app.codebook.map((g) => (g.id === gid ? { ...g, open: !g.open } : g));
  }

  function renameGroup(gid, newName) {
    if (!newName.trim()) return;
    const updated = app.codebook.map((g) => g.id === gid ? { ...g, name: newName.trim() } : g);
    app.codebook = updated;
    persistDebounced(updated);
  }

  function updateGroupDesc(gid, newDesc) {
    const updated = app.codebook.map((g) => g.id === gid ? { ...g, desc: newDesc } : g);
    app.codebook = updated;
    persistDebounced(updated);
  }

  function renameCode(cid, newName) {
    if (!newName.trim()) return;
    const updated = app.codebook.map((g) => ({
      ...g,
      children: g.children.map((c) => (c.id === cid ? { ...c, name: newName } : c))
    }));
    app.codebook = updated;
    persistDebounced(updated);
  }

  function updateCodeDesc(cid, newDesc) {
    const updated = app.codebook.map((g) => ({
      ...g,
      children: g.children.map((c) => c.id === cid ? { ...c, desc: newDesc } : c)
    }));
    app.codebook = updated;
    persistDebounced(updated);
  }

  function addGroup() {
    const name = newGroupName.trim();
    if (!name) return;
    const newGroup = {
      id: `g_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      name,
      color: newGroupColor,
      count: 0,
      open: true,
      desc: '',
      children: []
    };
    const updated = [...app.codebook, newGroup];
    app.codebook = updated;
    newGroupName = '';
    newGroupColor = '1';
    addingGroup = false;
    persistNow(updated);
  }

  function addChildToGroup(gid) {
    const name = prompt('Code name:');
    if (!name?.trim()) return;
    const group = app.codebook.find((g) => g.id === gid);
    const color = group?.color ?? '1';
    const newCode = {
      id: `c_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      name: name.trim(),
      color,
      count: 0,
      desc: ''
    };
    const updated = app.codebook.map((g) =>
      g.id === gid ? { ...g, children: [...g.children, newCode] } : g
    );
    app.codebook = updated;
    persistNow(updated);
  }

  function removeGroup(gid) {
    if (!confirm('Delete this code group?')) return;
    const updated = app.codebook.filter((g) => g.id !== gid);
    app.codebook = updated;
    menuOpenId = null;
    persistNow(updated);
  }

  function removeChild(cid) {
    const updated = app.codebook.map((g) => ({
      ...g,
      children: g.children.filter((c) => c.id !== cid)
    }));
    app.codebook = updated;
    persistNow(updated);
  }

  async function handleGenerate() {
    if (!app.activeFile) { app.toast('No transcript selected'); return; }
    generating = true;
    try {
      const turns = await getTranscript(app.activeFile);
      const text = turns.map(t =>
        `${t.speaker || 'Speaker'}: ` + (t.segments || []).map(s => s.t).join(' ')
      ).join('\n');
      const result = await generateCodebook(text);
      app.codebook = result.codebook;
      await refreshCodebookList();
    } catch (e) {
      app.toast(`Generate failed: ${e.message}`);
    } finally {
      generating = false;
    }
  }

  async function handleDeductive() {
    if (!app.researchQuestion.trim()) {
      app.toast('Set a research question in the context settings first', 'error');
      app.highlightRQ = true;
      return;
    }
    deducting = true;
    try {
      const result = await generateDeductiveCodebook(app.researchQuestion);
      app.codebook = result.codebook;
      await refreshCodebookList();
    } catch (e) {
      app.toast(`Deductive generation failed: ${e.message}`);
    } finally {
      deducting = false;
    }
  }

  async function handleAutoAnnotate() {
    if (!app.activeFile) { app.toast('No transcript selected'); return; }
    annotating = true;
    try {
      const { turns } = await autoAnnotateTranscript(app.activeFile);
      const updatedBook = codebookWithCounts(app.codebook, turns);
      app.codebook = updatedBook;
      await saveCodebook(updatedBook);
      app.bumpTranscriptVersion();
    } catch (e) {
      app.toast(`Auto annotation failed: ${e.message}`);
    } finally {
      annotating = false;
    }
  }

  let mergeModalOpen = $state(false);
  let mergeSelected = $state(/** @type {Set<string>} */ (new Set()));
  let merging = $state(false);

  function openMergeModal() {
    mergeSelected = new Set();
    mergeModalOpen = true;
  }

  function closeMergeModal() {
    mergeModalOpen = false;
  }

  function toggleMergeSelect(id) {
    const next = new Set(mergeSelected);
    if (next.has(id)) next.delete(id); else next.add(id);
    mergeSelected = next;
  }

  async function confirmMerge() {
    if (mergeSelected.size < 2) { app.toast('Select at least two codebooks to merge'); return; }
    merging = true;
    try {
      await mergeCodebooks([...mergeSelected]);
      await refreshCodebookList();
      app.codebook = await getCodebook();
      mergeModalOpen = false;
    } catch (e) {
      app.toast(`Merge failed: ${e.message}`);
    } finally {
      merging = false;
    }
  }

  let totalCount = $derived(app.codebook.reduce((n, g) => n + g.count, 0));

  let filtered = $derived.by(() => {
    if (!query.trim()) return app.codebook;
    const q = query.toLowerCase();
    return app.codebook
      .map((g) => ({
        ...g, open: true,
        children: g.children.filter(
          (c) => c.name.toLowerCase().includes(q) || (c.desc || '').toLowerCase().includes(q)
        )
      }))
      .filter((g) => g.children.length || g.name.toLowerCase().includes(q));
  });

  onMount(async () => {
    try {
      const [book] = await Promise.all([getCodebook(), refreshCodebookList()]);
      app.codebook = book;
    } catch (e) {
      app.toast(`Could not load codebook: ${e.message}`);
    }
  });

  // Close menus on outside click
  function onWindowClick(e) {
    if (menuOpenId && !/** @type {HTMLElement} */(e.target).closest('.cb-menu')) {
      menuOpenId = null;
    }
    if (cbMenuOpen && !/** @type {HTMLElement} */(e.target).closest('.cb-switcher')) {
      cbMenuOpen = false;
    }
  }
</script>

<svelte:window onclick={onWindowClick} />

<div class="pane elev" class:menu-open={menuOpenId !== null || cbMenuOpen}>
  <div class="pane-hd">
  <!-- 
      <span class="lbl">Codebook · {totalCount}</span> legacy count  
  -->
    <span class="lbl">Codebook</span>
    <div class="actions">
    <!-- Sort disabled for now, might reintroduce later
       <button class="iconbtn" title="Sort"><Icon name="sort" /></button>
    -->

      <button class="iconbtn" title="New group" onclick={() => { addingGroup = !addingGroup; }}>
        <Icon name="plus" />
      </button>
    </div>
  </div>
  <div class="cb-switcher-row">
    <div class="cb-switcher">
      <button class="cb-switcher-btn" onclick={() => (cbMenuOpen = !cbMenuOpen)}>
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <span
          class="cb-switcher-name"
          contenteditable={renamingCodebook}
          role="textbox"
          tabindex="-1"
          ondblclick={(e) => { e.stopPropagation(); startRenameCodebook(e); }}
          onclick={(e) => { if (renamingCodebook) e.stopPropagation(); }}
          onblur={(e) => finishRenameCodebook(/** @type {HTMLElement} */ (e.target).textContent)}
          onkeydown={(e) => {
            if (e.key === 'Enter') { e.preventDefault(); /** @type {HTMLElement} */ (e.target).blur(); }
            if (e.key === 'Escape') { /** @type {HTMLElement} */ (e.target).textContent = activeCodebookName; /** @type {HTMLElement} */ (e.target).blur(); }
          }}
        >{activeCodebookName}</span>
        <Icon name="chev-down" size={10} />
      </button>
      {#if cbMenuOpen}
        <div class="cb-switcher-dropdown" role="menu">
          {#each codebooks as cb (cb.id)}
            <div class="cb-switcher-item" class:active={cb.id === app.activeCodebookId}>
              <button role="menuitem" onclick={() => switchCodebook(cb.id)}>{cb.name}</button>
              <button
                class="cb-switcher-del"
                title="Delete codebook"
                onclick={(e) => handleDeleteCodebook(cb.id, e)}
              >✕</button>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
  <div class="cb-search">
    <input placeholder="Filter codes…" bind:value={query} />
  </div>

  <div class="pane-body">
    {#if addingGroup}
      <div class="cb-add-group">
        <input
          class="cb-add-input"
          placeholder="Group name…"
          bind:value={newGroupName}
          onkeydown={(e) => { if (e.key === 'Enter') addGroup(); if (e.key === 'Escape') addingGroup = false; }}
          autofocus
        />
        <div class="cb-color-row">
          {#each COLORS as c}
            <button
              class="cb-color-swatch"
              class:selected={newGroupColor === c}
              style="--c: var(--code-{c})"
              onclick={() => (newGroupColor = c)}
            ></button>
          {/each}
        </div>
        <div class="cb-add-actions">
          <button class="primary" onclick={addGroup}>Add group</button>
          <button onclick={() => (addingGroup = false)}>Cancel</button>
        </div>
      </div>
    {/if}

    <div class="cb-tree">
      {#each filtered as g (g.id)}
        <div class="cb-group">
          <div
            class="cb-parent"
            class:open={g.open}
            onclick={(e) => { if (!/** @type {HTMLElement} */(e.target).closest('.body')) toggleGroup(g.id); }}
            role="button"
            tabindex="0"
            onkeydown={(e) => e.key === 'Enter' && toggleGroup(g.id)}
          >
            <span class="caret"><Icon name="chev-right" /></span>
            <span class="sw" style="--c: var(--code-{g.color})"></span>
            <div class="body">
              <span
                class="name"
                contenteditable={editing?.id === g.id && editing?.field === 'name'}
                ondblclick={(e) => { e.stopPropagation(); editing = { id: g.id, field: 'name' }; setTimeout(() => /** @type {HTMLElement} */ (e.target).focus(), 0); }}
                onblur={(e) => { renameGroup(g.id, /** @type {HTMLElement} */ (e.target).textContent || g.name); editing = null; }}
                onkeydown={(e) => { if (e.key === 'Enter') { e.preventDefault(); /** @type {HTMLElement} */ (e.target).blur(); } if (e.key === 'Escape') { /** @type {HTMLElement} */ (e.target).textContent = g.name; /** @type {HTMLElement} */ (e.target).blur(); } }}
              >{g.name}</span>
              <span
                class="desc"
                class:visible={expandedDescs.has(g.id)}
                contenteditable={editing?.id === g.id && editing?.field === 'desc'}
                ondblclick={(e) => { e.stopPropagation(); editing = { id: g.id, field: 'desc' }; setTimeout(() => /** @type {HTMLElement} */ (e.target).focus(), 0); }}
                onblur={(e) => { updateGroupDesc(g.id, /** @type {HTMLElement} */ (e.target).textContent.trim()); editing = null; }}
                onkeydown={(e) => { if (e.key === 'Escape') { /** @type {HTMLElement} */ (e.target).textContent = g.desc || ''; /** @type {HTMLElement} */ (e.target).blur(); } }}
              >{g.desc || ''}</span>
            </div>
            <span class="count">{g.count}</span>
            <button
              class="iconbtn info-btn"
              class:active={expandedDescs.has(g.id)}
              title="Description"
              onclick={(e) => { e.stopPropagation(); toggleDesc(g.id); }}
            ><Icon name="info" size={11} /></button>
            <div class="cb-menu" style="position:relative;">
              <button
                class="iconbtn"
                onclick={(e) => { e.stopPropagation(); menuOpenId = menuOpenId === g.id ? null : g.id; }}
              ><Icon name="more" /></button>
              {#if menuOpenId === g.id}
                <div class="cb-dropdown" role="menu">
                  <button role="menuitem" onclick={(e) => { e.stopPropagation(); addChildToGroup(g.id); menuOpenId = null; }}>
                    + Add code
                  </button>
                  <button role="menuitem" class="danger" onclick={(e) => { e.stopPropagation(); removeGroup(g.id); }}>
                    Delete group
                  </button>
                </div>
              {/if}
            </div>
          </div>
          {#if g.open}
            <div class="cb-children">
              {#each g.children as c (c.id)}
                {@const active = app.activeCode === c.id}
                <!-- svelte-ignore a11y_no_static_element_interactions -->
                <div
                  class="cb-code"
                  class:active
                  draggable="true"
                  ondragstart={(e) => {
                    e.dataTransfer.effectAllowed = 'copy';
                    e.dataTransfer.setData('application/x-qualscope-code', c.id);
                    e.dataTransfer.setData('text/plain', c.id);
                  }}
                  onmouseenter={() => (app.activeCode = c.id)}
                  onmouseleave={() => { if (app.activeCode === c.id) app.activeCode = null; }}
                >
                  <span></span>
                  <span class="sw" style="--c: var(--code-{c.color})"></span>
                  <div class="body">
                    <span
                      class="name"
                      contenteditable={editing?.id === c.id && editing?.field === 'name'}
                      ondblclick={(e) => {
                        e.stopPropagation();
                        editing = { id: c.id, field: 'name' };
                        setTimeout(() => /** @type {HTMLElement} */ (e.target).focus(), 0);
                      }}
                      onblur={(e) => {
                        renameCode(c.id, /** @type {HTMLElement} */ (e.target).textContent || c.name);
                        editing = null;
                      }}
                      onkeydown={(e) => {
                        if (e.key === 'Enter') { e.preventDefault(); /** @type {HTMLElement} */ (e.target).blur(); }
                        if (e.key === 'Escape') { /** @type {HTMLElement} */ (e.target).textContent = c.name; /** @type {HTMLElement} */ (e.target).blur(); }
                      }}
                    >{c.name}</span>
                    <!-- svelte-ignore a11y_no_static_element_interactions -->
                    <span
                      class="desc"
                      class:visible={expandedDescs.has(c.id)}
                      contenteditable={editing?.id === c.id && editing?.field === 'desc'}
                      ondblclick={(e) => {
                        e.stopPropagation();
                        editing = { id: c.id, field: 'desc' };
                        setTimeout(() => /** @type {HTMLElement} */ (e.target).focus(), 0);
                      }}
                      onblur={(e) => {
                        updateCodeDesc(c.id, /** @type {HTMLElement} */ (e.target).textContent.trim());
                        editing = null;
                      }}
                      onkeydown={(e) => {
                        if (e.key === 'Escape') { /** @type {HTMLElement} */ (e.target).textContent = c.desc || ''; /** @type {HTMLElement} */ (e.target).blur(); }
                      }}
                    >{c.desc || ''}</span>
                  </div>
                  <span class="count">{c.count}</span>
                  <button
                    class="iconbtn info-btn"
                    class:active={expandedDescs.has(c.id)}
                    title="Description"
                    onclick={(e) => { e.stopPropagation(); toggleDesc(c.id); }}
                  ><Icon name="info" size={11} /></button>
                  <button
                    class="iconbtn del-code"
                    title="Delete code"
                    onclick={(e) => { e.stopPropagation(); removeChild(c.id); }}
                  >✕</button>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/each}

    </div>

    <div class="cb-foot-wrap">
      <div class="cb-foot">
        <button class="primary" onclick={handleGenerate} disabled={generating || deducting || annotating}>
          {generating ? 'generating…' : '✦ Generate'}
        </button>
        <button class="primary" onclick={handleDeductive} disabled={deducting || generating || annotating}>
          {deducting ? 'generating…' : '✦ Deductive'}
        </button>
        <button class="primary" onclick={handleAutoAnnotate} disabled={annotating || generating || deducting}>
          {annotating ? 'Applying Codes…' : '✦ Apply Codes'}
        </button>
      </div>
      <div class="cb-foot">
        <button class="primary" onclick={openMergeModal} disabled={generating || deducting || annotating || codebooks.length < 2}>
          ⋈ Merge codebooks
        </button>
      </div>
    </div>
  </div>
</div>

{#if mergeModalOpen}
  <div
    class="modal-backdrop"
    role="presentation"
    onclick={(e) => { if (e.target === e.currentTarget) closeMergeModal(); }}
  >
    <div class="modal" role="dialog" aria-modal="true" tabindex="-1">
      <div class="modal-hd">Merge codebooks</div>
      <div class="modal-body">
        {#if codebooks.length < 2}
          <p class="modal-hint">You need at least two codebooks to merge.</p>
        {:else}
          <p class="modal-hint">Select the codebooks to merge into a new one.</p>
          <div class="merge-list">
            {#each codebooks as cb (cb.id)}
              <label class="merge-item">
                <input
                  type="checkbox"
                  checked={mergeSelected.has(cb.id)}
                  onchange={() => toggleMergeSelect(cb.id)}
                />
                <span>{cb.name}</span>
              </label>
            {/each}
          </div>
        {/if}
      </div>
      <div class="modal-ft">
        <button onclick={closeMergeModal} disabled={merging}>Cancel</button>
        <button
          class="primary"
          onclick={confirmMerge}
          disabled={merging || mergeSelected.size < 2}
        >
          {merging ? 'Merging…' : 'OK'}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .menu-open { position: relative; z-index: 10; }
  .cb-switcher-row {
    padding: 6px 8px;
    border-bottom: 1px solid var(--hair);
  }
  .cb-switcher { position: relative; }
  .cb-switcher-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    width: 100%;
    padding: 4px 6px;
    font: inherit;
    font-size: 12px;
    color: var(--ink);
    background: var(--bg-sunk);
    border: 1px solid var(--hair);
    border-radius: 4px;
    cursor: pointer;
    text-align: left;
  }
  .cb-switcher-btn :global(svg) { margin-left: auto; opacity: 0.6; }
  .cb-switcher-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    outline: none;
  }
  .cb-switcher-name[contenteditable="true"] {
    background: var(--bg-elev);
    border-radius: 3px;
    padding: 0 2px;
  }
  .cb-switcher-dropdown {
    position: absolute;
    left: 0; right: 0; top: calc(100% + 2px);
    background: var(--bg-elev);
    border: 1px solid var(--hair);
    border-radius: 6px;
    box-shadow: 0 4px 12px oklch(0 0 0 / 0.15);
    z-index: 100;
    overflow: hidden;
    max-height: 220px;
    overflow-y: auto;
  }
  .cb-switcher-item {
    display: flex;
    align-items: center;
  }
  .cb-switcher-item.active { background: var(--bg-sunk); }
  .cb-switcher-item button[role="menuitem"] {
    flex: 1;
    text-align: left;
    padding: 6px 10px;
    font: inherit;
    font-size: 11.5px;
    color: var(--ink-2);
    background: none;
    border: none;
    cursor: pointer;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .cb-switcher-item button[role="menuitem"]:hover { background: var(--bg-sunk); color: var(--ink); }
  .cb-switcher-del {
    padding: 6px 10px;
    font-size: 9px;
    color: var(--ink-4);
    background: none;
    border: none;
    cursor: pointer;
  }
  .cb-switcher-del:hover { color: oklch(0.6 0.15 30); }
  .cb-add-group {
    padding: 8px;
    border-bottom: 1px solid var(--hair);
    background: var(--bg-sunk);
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .cb-add-input {
    font: inherit;
    font-size: 12px;
    padding: 4px 6px;
    background: var(--bg-elev);
    border: 1px solid var(--hair);
    border-radius: 4px;
    color: var(--ink);
    outline: none;
  }
  .cb-add-input:focus { border-color: var(--accent); }
  .cb-color-row { display: flex; gap: 4px; }
  .cb-color-swatch {
    width: 14px; height: 14px;
    border-radius: 3px;
    border: 2px solid transparent;
    background: oklch(var(--c) / 0.6);
    cursor: pointer;
  }
  .cb-color-swatch.selected { border-color: var(--ink-2); }
  .cb-add-actions { display: flex; gap: 6px; }
  .cb-dropdown {
    position: absolute;
    right: 0; top: calc(100% + 2px);
    background: var(--bg-elev);
    border: 1px solid var(--hair);
    border-radius: 6px;
    box-shadow: 0 4px 12px oklch(0 0 0 / 0.15);
    min-width: 130px;
    z-index: 100;
    overflow: hidden;
  }
  .cb-dropdown button {
    display: block;
    width: 100%;
    text-align: left;
    padding: 6px 10px;
    font: inherit;
    font-size: 11.5px;
    color: var(--ink-2);
    background: none;
    border: none;
    cursor: pointer;
  }
  .cb-dropdown button:hover { background: var(--bg-sunk); color: var(--ink); }
  .cb-dropdown button.danger { color: oklch(0.6 0.15 30); }
  .cb-dropdown button.danger:hover { background: oklch(0.6 0.15 30 / 0.1); }
  .del-code { opacity: 0; font-size: 9px; color: var(--ink-4); }
  .cb-code:hover .del-code { opacity: 1; }
  .cb-code[draggable="true"] { cursor: grab; }
  .cb-code[draggable="true"]:active { cursor: grabbing; }

  .cb-foot-wrap {
    position: sticky; bottom: 0;
    background: linear-gradient(to top, var(--bg-elev) 60%, transparent);
    padding: 16px 12px 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .cb-foot-wrap .cb-foot {
    position: static;
    background: none;
    padding: 0;
  }

  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: oklch(0 0 0 / 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  .modal {
    width: 320px;
    max-height: 70vh;
    display: flex;
    flex-direction: column;
    background: var(--bg-elev);
    border: 1px solid var(--hair);
    border-radius: 8px;
    box-shadow: 0 8px 24px oklch(0 0 0 / 0.25);
  }
  .modal-hd {
    padding: 12px 14px;
    font-size: 12.5px;
    font-weight: 600;
    color: var(--ink);
    border-bottom: 1px solid var(--hair);
  }
  .modal-body {
    padding: 10px 14px;
    overflow-y: auto;
  }
  .modal-hint {
    font-size: 11.5px;
    color: var(--ink-3);
    margin: 0 0 8px;
  }
  .merge-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .merge-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 2px;
    font-size: 12px;
    color: var(--ink-2);
    cursor: pointer;
  }
  .merge-item input { cursor: pointer; }
  .modal-ft {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 10px 14px;
    border-top: 1px solid var(--hair);
  }
</style>
