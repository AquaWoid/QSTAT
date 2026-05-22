<script>
  import { onMount } from 'svelte';
  import { streamChat } from '$lib/api.js';
  import { parseBlocks, inlineHtml } from '$lib/markdown.js';
  import Citation from './Citation.svelte';
  import SourcesUsed from './SourcesUsed.svelte';
  import { app } from '$lib/state.svelte.js';

  /** @type {{ messages: Array<{role:string,content:string}>, model: string, rag: {on:boolean,scope:string}, onDone?: (citeIds:number[], text:string) => void }} */
  let { messages, model, rag, onDone } = $props();

  let tokens = $state('');
  let citeIds = $state(/** @type {number[]} */ ([]));
  let done = $state(false);
  let error = $state('');

  const _messages = messages;
  const _model = model;
  const _rag = rag;

  onMount(() => {
    (async () => {
      try {
        for await (const ev of streamChat({ messages: _messages, model: _model, rag: _rag })) {
          if (ev.type === 'token') tokens += ev.value;
          else if (ev.type === 'cite') {
            app.registerCite(ev.value.id, ev.value);
            citeIds = [...citeIds, ev.value.id];
          } else if (ev.type === 'done') {
            done = true;
            onDone?.(citeIds, tokens);
          }
        }
      } catch (e) {
        error = e.message ?? 'Stream error';
        done = true;
        onDone?.(citeIds, tokens);
      }
    })();
  });

  let blocks = $derived(parseBlocks(tokens));
  let lastIdx = $derived(blocks.length - 1);
</script>

{#if error}
  <p style="color:oklch(0.6 0.15 30);font-family:var(--f-mono);font-size:11px;">[{error}]</p>
{:else}
  {#each blocks as block, bi}
    {#if block.kind === 'h3'}
      <h3>{#each block.parts as p}{#if p.kind === 'cite'}<Citation id={p.id} />{:else}{@html inlineHtml(p.value)}{/if}{/each}</h3>
    {:else if block.kind === 'h4'}
      <h4>{#each block.parts as p}{#if p.kind === 'cite'}<Citation id={p.id} />{:else}{@html inlineHtml(p.value)}{/if}{/each}</h4>
    {:else if block.kind === 'ul'}
      <ul>{#each block.items as item}<li>{#each item as p}{#if p.kind === 'cite'}<Citation id={p.id} />{:else}{@html inlineHtml(p.value)}{/if}{/each}</li>{/each}</ul>
    {:else if block.kind === 'ol'}
      <ol>{#each block.items as item}<li>{#each item as p}{#if p.kind === 'cite'}<Citation id={p.id} />{:else}{@html inlineHtml(p.value)}{/if}{/each}</li>{/each}</ol>
    {:else if block.kind === 'bq'}
      <blockquote>{#each block.parts as p}{#if p.kind === 'cite'}<Citation id={p.id} />{:else}{@html inlineHtml(p.value)}{/if}{/each}</blockquote>
    {:else}
      <p class:caret-blink={!done && bi === lastIdx}>
        {#each block.parts as p}{#if p.kind === 'cite'}<Citation id={p.id} />{:else}{@html inlineHtml(p.value)}{/if}{/each}
      </p>
    {/if}
  {/each}

  {#if !done && !tokens}
    <span class="caret-blink" style="display:inline-block;"></span>
  {/if}

  {#if done && citeIds.length}
    <SourcesUsed cites={citeIds} />
  {/if}
{/if}
