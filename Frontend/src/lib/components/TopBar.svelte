<script>
  import Icon from '$lib/Icon.svelte';
  import { app } from '$lib/state.svelte.js';

  let { project } = $props();

  let codeCount = $derived(
    app.codebook.reduce((n, g) => n + 1 + g.children.length, 0)
  );
  let transcriptCount = $derived(
    app.files.filter((f) => f.type === 'mp3' && f.status === 'ok').length
  );
  let procCount = $derived(
    app.files.filter((f) => f.status === 'proc').length
  );
</script>

<div class="topbar">
  <div class="brand">
    <span class="mark">Q</span>
    <b>QualScope</b>
  </div>
  <div class="crumbs">
    <span>{project.name}</span>
  </div>
  <div class="status">
    {#if procCount > 0}
      <span><span class="dot proc"></span>{procCount} processing…</span>
    {:else}
      <span><span class="dot"></span>ready</span>
    {/if}
    <span>{app.files.length} files · {codeCount} codes · {transcriptCount} transcripts</span>
  </div>
  <button class="iconbtn" title="Refresh"><Icon name="refresh" /></button>
  <button class="iconbtn" title="Settings"><Icon name="settings" /></button>
</div>

<style>
  .dot.proc { background: oklch(0.65 0.15 80); }
</style>
