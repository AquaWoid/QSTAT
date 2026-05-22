<script>
  import { onMount } from 'svelte';
  import Icon from '$lib/Icon.svelte';
  import { app } from '$lib/state.svelte.js';
  import { getCodebook, updateCode, suggestCodes } from '$lib/api.js';

  let query = $state('');
  let editingId = $state(/** @type {string | null} */ (null));
  let suggesting = $state(false);
  let proposed = $state(/** @type {Array<{name:string,desc:string,color:string}>} */ ([]));

  // Debounce timer per code ID
  const _debounces = new Map();

  function toggleGroup(gid) {
    app.codebook = app.codebook.map((g) => (g.id === gid ? { ...g, open: !g.open } : g));
  }

  function renameCode(cid, newName) {
    app.codebook = app.codebook.map((g) => ({
      ...g,
      children: g.children.map((c) => (c.id === cid ? { ...c, name: newName } : c))
    }));
    // Debounced PATCH
    clearTimeout(_debounces.get(cid));
    _debounces.set(cid, setTimeout(async () => {
      try {
        await updateCode(cid, { name: newName });
      } catch (e) {
        app.toast(`Failed to save rename: ${e.message}`);
      }
    }, 400));
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

  async function handleSuggest() {
    suggesting = true;
    proposed = [];
    try {
      const suggestions = await suggestCodes(app.activeFile, app.codebook);
      proposed = suggestions;
    } catch (e) {
      app.toast(`Suggest failed: ${e.message}`);
    } finally {
      suggesting = false;
    }
  }

  function acceptProposal(p, idx) {
    // Add as a new group (no parent yet) or pick the first group as parent
    const newCode = {
      id: `c_${Date.now()}`,
      name: p.name,
      color: p.color || '1',
      count: 0,
      desc: p.desc || ''
    };
    // For now append as a new single-child group
    const newGroup = {
      id: `g_${Date.now()}`,
      name: p.name,
      color: p.color || '1',
      count: 0,
      open: true,
      desc: p.desc || '',
      children: []
    };
    app.codebook = [...app.codebook, newGroup];
    proposed = proposed.filter((_, i) => i !== idx);
  }

  function dismissProposal(idx) {
    proposed = proposed.filter((_, i) => i !== idx);
  }

  onMount(async () => {
    try {
      const book = await getCodebook();
      if (book.length > 0) app.codebook = book;
    } catch (e) {
      app.toast(`Could not load codebook: ${e.message}`);
    }
  });
</script>

<div class="pane elev">
  <div class="pane-hd">
    <span class="lbl">Codebook · {totalCount}</span>
    <div class="actions">
      <button class="iconbtn" title="Sort"><Icon name="sort" /></button>
      <button class="iconbtn" title="New code"><Icon name="plus" /></button>
    </div>
  </div>
  <div class="cb-search">
    <input placeholder="Filter codes…" bind:value={query} />
  </div>

  <div class="pane-body">
    <div class="cb-tree">
      {#each filtered as g (g.id)}
        <div class="cb-group">
          <div
            class="cb-parent"
            class:open={g.open}
            onclick={() => toggleGroup(g.id)}
            role="button"
            tabindex="0"
            onkeydown={(e) => e.key === 'Enter' && toggleGroup(g.id)}
          >
            <span class="caret"><Icon name="chev-right" /></span>
            <span class="sw" style="--c: var(--code-{g.color})"></span>
            <span class="name">{g.name}</span>
            <span class="count">{g.count}</span>
            <button class="iconbtn" onclick={(e) => e.stopPropagation()}><Icon name="more" /></button>
          </div>
          {#if g.open}
            <div class="cb-children">
              {#each g.children as c (c.id)}
                {@const active = app.activeCode === c.id}
                <!-- svelte-ignore a11y_no_static_element_interactions -->
                <div
                  class="cb-code"
                  class:active
                  class:expanded={active}
                  onmouseenter={() => (app.activeCode = c.id)}
                  onmouseleave={() => (app.activeCode = null)}
                >
                  <span></span>
                  <span class="sw" style="--c: var(--code-{c.color})"></span>
                  <div class="body">
                    <span
                      class="name"
                      contenteditable={editingId === c.id}
                      ondblclick={(e) => {
                        e.stopPropagation();
                        editingId = c.id;
                        setTimeout(() => /** @type {HTMLElement} */ (e.target).focus(), 0);
                      }}
                      onblur={(e) => {
                        renameCode(c.id, /** @type {HTMLElement} */ (e.target).textContent || c.name);
                        editingId = null;
                      }}
                      onkeydown={(e) => {
                        if (e.key === 'Enter') { e.preventDefault(); /** @type {HTMLElement} */ (e.target).blur(); }
                      }}
                    >{c.name}</span>
                    {#if c.desc}<span class="desc">{c.desc}</span>{/if}
                  </div>
                  <span class="count">{c.count}</span>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/each}

      {#if proposed.length}
        <div class="cb-proposed">
          <div class="cb-proposed-hd">Suggested codes</div>
          {#each proposed as p, i (i)}
            <div class="cb-code proposed">
              <span></span>
              <span class="sw" style="--c: var(--code-{p.color || '1'})"></span>
              <div class="body">
                <span class="name">{p.name}</span>
                {#if p.desc}<span class="desc">{p.desc}</span>{/if}
              </div>
              <button class="iconbtn accept" onclick={() => acceptProposal(p, i)} title="Add to codebook">✓</button>
              <button class="iconbtn" onclick={() => dismissProposal(i)} title="Dismiss">✕</button>
            </div>
          {/each}
        </div>
      {/if}
    </div>

    <div class="cb-foot">
      <button>Merge…</button>
      <button>Export</button>
      <button class="primary" onclick={handleSuggest} disabled={suggesting}>
        {suggesting ? 'suggesting…' : '✦ Suggest codes'}
      </button>
    </div>
  </div>
</div>

<style>
  .cb-proposed {
    margin-top: 8px;
    border-top: 1px solid var(--hair);
    padding-top: 4px;
  }
  .cb-proposed-hd {
    font-family: var(--f-mono);
    font-size: 9.5px;
    color: var(--ink-3);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding: 4px 8px 2px;
  }
  .cb-code.proposed {
    opacity: 0.85;
    border-left: 2px dashed var(--accent);
  }
  .iconbtn.accept {
    color: oklch(0.55 0.12 150);
    font-size: 10px;
  }
</style>
