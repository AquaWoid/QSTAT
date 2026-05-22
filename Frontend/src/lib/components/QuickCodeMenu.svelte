<script>
  import { onMount } from 'svelte';

  /** @type {{ codebook: any[], pos: { x: number, y: number }, onclose: () => void }} */
  let { codebook, pos, onclose } = $props();

  let menu = $state();

  // Top 6 most-applied codes
  let top = $derived(
    codebook
      .flatMap((g) => g.children.map((c) => ({ ...c, parent: g.name })))
      .sort((a, b) => (b.count || 0) - (a.count || 0))
      .slice(0, 6)
  );

  onMount(() => {
    const onDown = (e) => {
      if (menu && !menu.contains(e.target)) onclose();
    };
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  });
</script>

<div
  bind:this={menu}
  class="qcode"
  style="left: {Math.min(window.innerWidth - 220, Math.max(8, pos.x - 100))}px; top: {pos.y}px;"
>
  <div class="hd">Apply code</div>
  {#each top as c, i}
    <div class="item" onclick={onclose} role="button" tabindex="0" onkeydown={onclose}>
      <span class="sw" style="--c: var(--code-{c.color})"></span>
      <span>{c.name} <span style="color: var(--ink-4); font-size: 10px;">· {c.parent}</span></span>
      <span class="kbd">{i + 1}</span>
    </div>
  {/each}
  <div class="sep"></div>
  <div class="new" onclick={onclose} role="button" tabindex="0" onkeydown={onclose}>New code from selection…</div>
  <div class="new" onclick={onclose} role="button" tabindex="0" onkeydown={onclose} style="color: var(--accent);">
    <span style="width:14px; text-align:center;">✦</span>
    Suggest with LLM
  </div>
</div>
