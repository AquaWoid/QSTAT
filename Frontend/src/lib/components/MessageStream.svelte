<script>
  import { onMount } from 'svelte';
  import { streamChat } from '$lib/api.js';
  import Citation from './Citation.svelte';
  import SourcesUsed from './SourcesUsed.svelte';
  import { app } from '$lib/state.svelte.js';

  /** @type {{ messages: Array<{role:string,content:string}>, model: string, rag: {on:boolean,scope:string}, onDone?: (citeIds:number[]) => void }} */
  let { messages, model, rag, onDone } = $props();

  let tokens = $state('');
  let citeIds = $state(/** @type {number[]} */ ([]));
  let done = $state(false);
  let error = $state('');

  // Snapshot props at mount time so the effect only runs once
  const _messages = messages;
  const _model = model;
  const _rag = rag;

  onMount(() => {
    (async () => {
      try {
        for await (const ev of streamChat({ messages: _messages, model: _model, rag: _rag })) {
          if (ev.type === 'token') {
            tokens += ev.value;
          } else if (ev.type === 'cite') {
            app.registerCite(ev.value.id, ev.value);
            citeIds = [...citeIds, ev.value.id];
          } else if (ev.type === 'done') {
            done = true;
            onDone?.(citeIds);
          }
        }
      } catch (e) {
        error = e.message ?? 'Stream error';
        done = true;
      }
    })();
  });

  /**
   * Split accumulated tokens into renderable parts.
   * Paragraphs are separated by \n\n.
   * [^N] inline citation markers are converted to Citation components.
   */
  function parseParagraphs(text) {
    return text.split(/\n\n+/).filter(Boolean).map((para) => {
      const parts = [];
      const re = /\[\^(\d+)\]/g;
      let last = 0;
      let m;
      while ((m = re.exec(para)) !== null) {
        if (m.index > last) parts.push({ kind: 'text', value: para.slice(last, m.index) });
        parts.push({ kind: 'cite', id: Number(m[1]) });
        last = m.index + m[0].length;
      }
      if (last < para.length) parts.push({ kind: 'text', value: para.slice(last) });
      return parts;
    });
  }

  let paragraphs = $derived(parseParagraphs(tokens));
</script>

{#if error}
  <p style="color: oklch(0.6 0.15 30); font-family: var(--f-mono); font-size: 11px;">[{error}]</p>
{:else}
  {#each paragraphs as parts, pi}
    <p class:caret-blink={!done && pi === paragraphs.length - 1}>
      {#each parts as part}
        {#if part.kind === 'text'}{part.value}{:else}<Citation id={part.id} />{/if}
      {/each}
    </p>
  {/each}
  {#if !done && !tokens}
    <span class="caret-blink" style="display:inline-block;"></span>
  {/if}
  {#if done && citeIds.length}
    <SourcesUsed cites={citeIds} />
  {/if}
{/if}
