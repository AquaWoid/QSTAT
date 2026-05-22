<script>
  import Icon from '$lib/Icon.svelte';
  let { project } = $props();
</script>

<div class="topbar">
  <div class="brand">
    <span class="mark">Q</span>
    <b>QualScope</b>
  </div>
  <div class="crumbs">
    <span>{project.name}</span>
    <span class="sep">/</span>
    <span class="cur">{project.current}</span>
  </div>
  <div class="status">
    <span><span class="dot"></span>backend · ready</span>
    <span>{project.files.length} files · 169 codes · 12 transcripts</span>
  </div>
  <button class="iconbtn" title="Refresh"><Icon name="refresh" /></button>
  <button class="iconbtn" title="Settings"><Icon name="settings" /></button>
</div>
