<script>
  import Icon from '$lib/Icon.svelte';

  /** @type {{ f: { id: string, name: string, type: string, status: string, meta: string, progress?: number }, active: boolean, onpick: (id: string) => void, ondelete?: (id: string) => void }} */
  let { f, active, onpick, ondelete } = $props();

  const KIND = {
    mp3: { label: 'MP3', cls: 'audio' },
    pdf: { label: 'PDF', cls: '' },
    doc: { label: 'DOC', cls: '' },
    xls: { label: 'XLS', cls: '' }
  };

  let kind = $derived(KIND[f.type] ?? { label: f.type.toUpperCase(), cls: '' });
</script>

<div
  class="ctx-item"
  class:active
  title={f.name}
  onclick={() => onpick(f.id)}
  role="button"
  tabindex="0"
  onkeydown={(e) => e.key === 'Enter' && onpick(f.id)}
>
  <span class="ctx-icon {kind.cls}">{kind.cls ? '' : kind.label}</span>
  <span class="ctx-name">
    <span style="overflow:hidden;text-overflow:ellipsis;">{f.name}</span>
    <span class="meta">{f.meta}</span>
  </span>
  <div class="ctx-end">
    {#if f.status === 'proc'}
      <span class="ctx-badge proc">{f.progress}%</span>
    {:else if f.status === 'queue'}
      <span class="ctx-badge queue">queue</span>
    {/if}
    {#if ondelete}
      <button
        class="del-btn"
        title="Delete file"
        onclick={(e) => { e.stopPropagation(); ondelete(f.id); }}
      >
        <Icon name="trash" size={11} />
      </button>
    {/if}
  </div>
  {#if f.progress != null}
    <span class="ctx-progress"><span style="--p: {f.progress}%"></span></span>
  {/if}
</div>

<style>
  .ctx-end {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .del-btn {
    display: grid;
    place-items: center;
    width: 20px;
    height: 20px;
    padding: 0;
    border: none;
    background: none;
    color: var(--ink-4);
    border-radius: 3px;
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.1s, color 0.1s, background 0.1s;
  }

  :global(.ctx-item:hover) .del-btn {
    opacity: 1;
  }

  .del-btn:hover {
    color: oklch(0.55 0.18 25);
    background: oklch(0.55 0.18 25 / 0.1);
  }
</style>
