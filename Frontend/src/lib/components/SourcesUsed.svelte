<script>
  import { app } from '$lib/state.svelte.js';

  /** @type {{ cites: number[] }} */
  let { cites } = $props();

  let open = $state(false);

  let items = $derived(cites.map((id) => app.cites[id]).filter(Boolean));
  let docs  = $derived(items.filter((c) => c.kind === 'd'));
  let txs   = $derived(items.filter((c) => c.kind === 't'));

  let summary = $derived(
    [
      docs.length && `${docs.length} chunk${docs.length === 1 ? '' : 's'}`,
      txs.length  && `${txs.length} transcript ${txs.length === 1 ? 'ref' : 'refs'}`
    ]
      .filter(Boolean)
      .join(' · ')
  );

  let fileNames = $derived([...new Set(docs.map((d) => d.file))].slice(0, 2).join(', '));
</script>

<div class="sources">
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="sources-row"
    class:open
    onclick={() => (open = !open)}
    role="button"
    tabindex="0"
    onkeydown={(e) => e.key === 'Enter' && (open = !open)}
  >
    <span class="caret">{open ? '▾' : '▸'}</span>
    <span class="lbl">retrieved · {summary}</span>
    {#if fileNames}
      <span class="files">{fileNames}{docs.length > 2 ? `, +${docs.length - 2}` : ''}</span>
    {/if}
  </div>
  {#if open}
    <div class="sources-list">
      {#each cites as id}
        {@const c = app.cites[id]}
        {#if c}
          <!-- svelte-ignore a11y_no_static_element_interactions -->
          <div
            class="source-item"
            class:doc={c.kind === 'd'}
            class:tx={c.kind === 't'}
            onclick={() => app.cite(id)}
            role="button"
            tabindex="0"
            onkeydown={(e) => e.key === 'Enter' && app.cite(id)}
          >
            <span class="srcnum">{id}</span>
            <div class="srcbody">
              <div class="srchead">
                {#if c.kind === 'd'}
                  <span class="srcfile">{c.file}</span>
                  <span class="srcmeta">p.{c.page} · {c.score.toFixed(2)}</span>
                {:else}
                  <span class="srcfile">Interview 12 — Aldana</span>
                  <span class="srcmeta">{c.turnTs}</span>
                {/if}
              </div>
              {#if c.kind === 'd'}
                <div class="srcprev">{c.preview}</div>
              {/if}
            </div>
          </div>
        {/if}
      {/each}
    </div>
  {/if}
</div>
