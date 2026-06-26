<script>
  import { tick, onMount } from 'svelte';
  import Icon from '$lib/Icon.svelte';
  import Message from './Message.svelte';
  import MessageStream from './MessageStream.svelte';
  import Citation from './Citation.svelte';
  import SourcesUsed from './SourcesUsed.svelte';
  import { fetchModels, fetchConfig, patchConfig } from '$lib/api.js';
  import { app } from '$lib/state.svelte.js';
  import { parseBlocks, inlineHtml } from '$lib/markdown.js';

  /** @type {Array<{id:string, name:string, identifier:string, kind:string, desc:string}>} */
  let models = $state([]);
  let model = $state(/** @type {{id:string, name:string, identifier:string, kind:string, desc:string} | null} */ (null));
  let picker = $state(false);

  onMount(async () => {
    try {
      const [data, cfg] = await Promise.all([fetchModels(), fetchConfig().catch(() => ({}))]);
      const list = [];
      for (const [kind, entries] of Object.entries(data)) {
        if (kind === 'disabled' || kind === 'transcription') continue;
        for (const m of entries) {
          list.push({
            id: `${kind}-${m.identifier.replace(/[/.]/g, '-')}`,
            name: m.name,
            identifier: m.identifier,
            kind,
            desc: kind === 'local' ? 'local · vLLM' : `cloud · ${m.identifier.split('/')[0]}`
          });
        }
      }
      models = list;
      const saved = cfg?.activeModel?.identifier;
      model = (saved && list.find((m) => m.identifier === saved)) || list[0] || null;
    } catch (e) {
      console.error('[ChatPane] model load failed:', e);
    }
  });

  function selectModel(m) {
    model = m;
    picker = false;
    patchConfig({ activeModel: { identifier: m.identifier, kind: m.kind } }).catch(() => {});
  }
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

  async function copyThread() {
    if (!app.messages.length) return;
    const md = app.messages
      .map((msg) => {
        const who = msg.role === 'user' ? 'User' : 'QualScope';
        return `**${who}** _(${msg.ts})_\n\n${msg.content}`;
      })
      .join('\n\n---\n\n');
    await navigator.clipboard.writeText(md);
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
      onclick={() => models.length && (picker = !picker)}
      role="button"
      tabindex="0"
      onkeydown={(e) => e.key === 'Enter' && models.length && (picker = !picker)}
    >
      <span class="badge {model?.kind ?? ''}">{model?.kind ?? '…'}</span>
      <span class="name">{model?.name ?? 'loading…'}</span>
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
          {#each models as m (m.id)}
            <div
              class="item"
              onclick={() => selectModel(m)}
              role="menuitem"
              tabindex="0"
              onkeydown={(e) => e.key === 'Enter' && selectModel(m)}
            >
              <span class="badge {m.kind}">{m.kind}</span>
              <div class="item-info">
                <span class="item-name">{m.name}</span>
                <span class="item-desc">{m.desc}</span>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
    <div class="chat-actions">
      <button class="iconbtn" title="Copy thread" onclick={copyThread}><Icon name="copy" /></button>
      <button class="iconbtn" title="New thread" onclick={newThread}><Icon name="plus" /></button>

      <!-- Temporarly deactivated - Still have to think about what should be put in the context menu
      <button class="iconbtn" title="More"><Icon name="more" /></button>
      -->

     
    </div>
  </div>

  <div class="pane-body" bind:this={bodyEl}>
    <div class="chat-body">
      {#each app.messages as msg (msg.id)}
        {#if msg.role === 'user'}
          <Message role="user" who="LW" ts={msg.ts}>
            {msg.content}
          </Message>
        {:else if msg.id === streamingId}
          <Message role="assistant" who="QS" ts={msg.ts} model={model?.name}>
            <MessageStream
              messages={streamMessages}
              model={model?.identifier ?? ''}
              modelKind={model?.kind ?? 'cloud'}
              rag={{ on: ragOn, scope: ragScope }}
              onDone={onStreamDone}
            />
          </Message>
        {:else}
          <Message role="assistant" who="QS" ts={msg.ts} model={model?.name}>
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
        <!-- 
         {#if ragOn}
          <button class="rag-scope" onclick={cycleScope}>
            {#if ragScope === 'all'}<span>all {app.files.length} files</span>
            {:else if ragScope === 'transcript'}<span>this transcript only</span>
            {:else}<span>selected files</span>{/if}
          </button>
        {/if}       
        -->

        <span class="rag-hint">{ragOn ? 'top-8 chunks · Chroma' : 'no retrieval — pure reasoning'}</span>
      </div>
      <textarea
        placeholder="Ask about themes, codes, or quotes…  ctrl+↵ to send"
        bind:value={input}
        rows="2"
        onkeydown={onKeydown}
        disabled={isStreaming}
      ></textarea>
      <div class="row">
        <div class="slash">
        <!--
           <span class="cmd">/summarize</span>
          <span class="cmd">/find-themes</span>
          <span class="cmd">/cite</span>
          <span class="cmd">/contradict</span>         
        -->

        </div>
        <button class="send" onclick={send} disabled={isStreaming}>
          {isStreaming ? 'streaming…' : 'send'} <span class="k">ctrl+↵</span>
        </button>
      </div>
    </div>
  </div>
</div>
