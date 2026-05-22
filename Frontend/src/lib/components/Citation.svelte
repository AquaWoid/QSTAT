<script>
  import Icon from '$lib/Icon.svelte';
  import { app } from '$lib/state.svelte.js';

  /** @type {{ id: number }} */
  let { id } = $props();

  let cite = $derived(app.cites[id]);
  let isDoc = $derived(cite?.kind === 'd');
  let flash = $derived(app.citeFlash === id);
</script>

{#if cite}
  <span
    class="cite"
    class:doc={isDoc}
    style={flash ? 'background: var(--accent); color: var(--bg-elev);' : ''}
    title={isDoc ? `${cite.file} · p.${cite.page}` : `Transcript · ${cite.turnTs}`}
    onclick={() => app.cite(id)}
    role="button"
    tabindex="0"
    onkeydown={(e) => e.key === 'Enter' && app.cite(id)}
  >
    {#if isDoc}<Icon name="cite" size={9} />{/if}{id}
  </span>
{/if}
