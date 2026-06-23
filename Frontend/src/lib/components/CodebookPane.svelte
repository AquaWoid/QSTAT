<script>
  import { onMount } from 'svelte';
  import Icon from '$lib/Icon.svelte';
  import { app } from '$lib/state.svelte.js';
  import { getCodebook, saveCodebook, generateCodebook, generateDeductiveCodebook, getTranscript } from '$lib/api.js';

  let query = $state('');
  let editing = $state(/** @type {{id: string, field: 'name'|'desc'} | null} */ (null));
  let generating = $state(false);
  let deducting = $state(false);
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
      await generateCodebook(text);
      const book = await getCodebook();
      app.codebook = book;
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
      await generateDeductiveCodebook(app.researchQuestion);
      const book = await getCodebook();
      app.codebook = book;
    } catch (e) {
      app.toast(`Deductive generation failed: ${e.message}`);
    } finally {
      deducting = false;
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
      const book = await getCodebook();
      app.codebook = book;
    } catch (e) {
      app.toast(`Could not load codebook: ${e.message}`);
    }
  });

  // Close menu on outside click
  function onWindowClick(e) {
    if (menuOpenId && !/** @type {HTMLElement} */(e.target).closest('.cb-menu')) {
      menuOpenId = null;
    }
  }
</script>

<svelte:window onclick={onWindowClick} />

<div class="pane elev" class:menu-open={menuOpenId !== null}>
  <div class="pane-hd">
    <span class="lbl">Codebook · {totalCount}</span>
    <div class="actions">
    <!-- Sort disabled for now, might reintroduce later
       <button class="iconbtn" title="Sort"><Icon name="sort" /></button>     
    -->

      <button class="iconbtn" title="New group" onclick={() => { addingGroup = !addingGroup; }}>
        <Icon name="plus" />
      </button>
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

    <div class="cb-foot">
      <button class="primary" onclick={handleGenerate} disabled={generating || deducting}>
        {generating ? 'generating…' : '✦ Generate'}
      </button>
      <button class="primary" onclick={handleDeductive} disabled={deducting || generating}>
        {deducting ? 'generating…' : '✦ Deductive'}
      </button>
    </div>
  </div>
</div>

<style>
  .menu-open { position: relative; z-index: 10; }
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
</style>
