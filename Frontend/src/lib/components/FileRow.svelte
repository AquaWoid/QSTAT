<script>
  import Icon from '$lib/Icon.svelte';

  /** @type {{ f: { id: string, name: string, type: string, status: string, meta: string, progress?: number }, active: boolean, onpick: (id: string) => void }} */
  let { f, active, onpick } = $props();

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
  {#if f.status === 'proc'}
    <span class="ctx-badge proc">{f.progress}%</span>
  {:else if f.status === 'queue'}
    <span class="ctx-badge queue">queue</span>
  {/if}
  {#if f.progress != null}
    <span class="ctx-progress"><span style="--p: {f.progress}%"></span></span>
  {/if}
</div>
