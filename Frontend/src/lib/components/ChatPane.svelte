<script>
  import { tick } from 'svelte';
  import Icon from '$lib/Icon.svelte';
  import Message from './Message.svelte';
  import MessageStream from './MessageStream.svelte';
  import Citation from './Citation.svelte';
  import SourcesUsed from './SourcesUsed.svelte';
  import { MODELS } from '$lib/data.js';
  import { app } from '$lib/state.svelte.js';
  import { parseBlocks, inlineHtml } from '$lib/markdown.js';

  let model = $state(MODELS[0]);
  let picker = $state(false);
  let input = $state('');
  let ragOn = $state(true);
  let ragScope = $state('all');
  /** @type {string | null} ID of the message currently being streamed */
  let streamingId = $state(null);
  /** @type {HTMLDivElement} */
  let bodyEl;

  let isStreaming = $derived(streamingId !== null);

  const SCOPES = { all: 'transcript', transcript: 'selection', selection: 'all' };
  function cycleScope() { ragScope = SCOPES[ragScope]; }

  function scrollBottom() {
    tick().then(() => { if (bodyEl) bodyEl.scrollTop = bodyEl.scrollHeight; });
  }

  async function send() {
    const text = input.trim();
    if (!text || isStreaming) return;

    input = '';
    const ts = new Date().toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' });

    app.pushMessage({ role: 'user', content: text, id: `u_${Date.now()}`, ts });

    const aid = `a_${Date.now()}`;
    app.pushMessage({ role: 'assistant', content: '', id: aid, ts, streaming: true });
    streamingId = aid;

    scrollBottom();
  }

  function onStreamDone(citeIds, finalText) {
    app.finalizeMessage(streamingId, finalText, citeIds);
    streamingId = null;
    scrollBottom();
  }

  function onKeydown(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); send(); }
  }

  function newThread() {
    app.clearMessages();
    streamingId = null;
  }

  // Messages to pass to the live stream — everything before the streaming placeholder.
  let streamMessages = $derived.by(() => {
    if (!streamingId) return [];
    const msgs = app.messages;
    const idx = msgs.findIndex((m) => m.id === streamingId);
    if (idx <= 0) return [];
    return msgs.slice(0, idx).map((m) => ({ role: m.role, content: m.content }));
  });
</script>

<div class="pane">
  <div class="chat-hd">
    <div
      class="model-picker"
      style="position:relative;"
      onclick={() => (picker = !picker)}
      role="button"
      tabindex="0"
      onkeydown={(e) => e.key === 'Enter' && (picker = !picker)}
    >
      <span class="badge {model.kind}">{model.kind}</span>
      <span class="name">{model.name}</span>
      <span class="caret"><Icon name="chev-down" /></span>
      {#if picker}
        <div
          class="qcode"
          style="position:absolute; top:calc(100% + 6px); right:0; left:auto;"
          onmousedown={(e) => e.stopPropagation()}
          role="menu"
          tabindex="0"
        >
          <div class="hd">Model</div>
          {#each MODELS as m (m.id)}
            <div
              class="item"
              onclick={() => { model = m; picker = false; }}
              role="menuitem"
              tabindex="0"
              onkeydown={(e) => e.key === 'Enter' && (model = m)}
            >
              <span
                class="badge {m.kind}"
                style="font-family:var(--f-mono);font-size:8.5px;padding:1px 4px;border-radius:2px;letter-spacing:0.04em;text-transform:uppercase;width:auto;background:{m.kind==='local'?'oklch(0.50 0.10 150 / 0.13)':'oklch(0.50 0.13 250 / 0.13)'};color:{m.kind==='local'?'oklch(0.50 0.10 150)':'oklch(0.50 0.13 250)'};"
              >{m.kind}</span>
              <div style="display:flex;flex-direction:column;">
                <span>{m.name}</span>
                <span style="color:var(--ink-4);font-family:var(--f-mono);font-size:9.5px;">{m.desc}</span>
              </div>
              <span></span>
            </div>
          {/each}
        </div>
      {/if}
    </div>
    <div class="chat-actions">
      <button class="iconbtn" title="Copy thread"><Icon name="copy" /></button>
      <button class="iconbtn" title="New thread" onclick={newThread}><Icon name="plus" /></button>
      <button class="iconbtn" title="More"><Icon name="more" /></button>
    </div>
  </div>

  <div class="pane-body" bind:this={bodyEl}>
    <div class="chat-body">
      {#each app.messages as msg (msg.id)}
        {#if msg.role === 'user'}
          <Message role="user" who="RM" ts={msg.ts}>
            {msg.content}
          </Message>
        {:else if msg.id === streamingId}
          <Message role="assistant" who="QS" ts={msg.ts} model={model.name}>
            <MessageStream
              messages={streamMessages}
              model={model.name}
              rag={{ on: ragOn, scope: ragScope }}
              onDone={onStreamDone}
            />
          </Message>
        {:else}
          <Message role="assistant" who="QS" ts={msg.ts} model={model.name}>
            {#each parseBlocks(msg.content || '') as block}
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
                <p>{#each block.parts as p}{#if p.kind === 'cite'}<Citation id={p.id} />{:else}{@html inlineHtml(p.value)}{/if}{/each}</p>
              {/if}
            {/each}
            {#if msg.citeIds?.length}
              <SourcesUsed cites={msg.citeIds} />
            {/if}
          </Message>
        {/if}
      {/each}

      {#if !app.messages.length}
        <div style="padding:24px 16px; color:var(--ink-4); font-size:12px; text-align:center;">
          Ask about themes, codes, or quotes across your corpus.
        </div>
      {/if}
    </div>
  </div>

  <div class="chat-foot">
    <div class="chat-input">
      <div class="rag-row">
        <button
          class="rag-toggle"
          class:on={ragOn}
          onclick={() => (ragOn = !ragOn)}
          title="Toggle retrieval-augmented context"
        >
          <span class="dot"></span>@docs
        </button>
        {#if ragOn}
          <button class="rag-scope" onclick={cycleScope}>
            {#if ragScope === 'all'}<span>all {app.files.length} files</span>
            {:else if ragScope === 'transcript'}<span>this transcript only</span>
            {:else}<span>selected files</span>{/if}
          </button>
        {/if}
        <span class="rag-hint">{ragOn ? 'top-8 chunks · Chroma' : 'no retrieval — pure reasoning'}</span>
      </div>
      <textarea
        placeholder="Ask about themes, codes, or quotes…  ⌘↵ to send"
        bind:value={input}
        rows="2"
        onkeydown={onKeydown}
        disabled={isStreaming}
      ></textarea>
      <div class="row">
        <div class="slash">
          <span class="cmd">/summarize</span>
          <span class="cmd">/find-themes</span>
          <span class="cmd">/cite</span>
          <span class="cmd">/contradict</span>
        </div>
        <button class="send" onclick={send} disabled={isStreaming}>
          {isStreaming ? 'streaming…' : 'send'} <span class="k">⌘↵</span>
        </button>
      </div>
    </div>
  </div>
</div>
