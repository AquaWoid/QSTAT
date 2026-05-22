<script>
  import { tick } from 'svelte';
  import Icon from '$lib/Icon.svelte';
  import Message from './Message.svelte';
  import MessageStream from './MessageStream.svelte';
  import { MODELS } from '$lib/data.js';
  import { app } from '$lib/state.svelte.js';

  let model = $state(MODELS[0]);
  let picker = $state(false);
  let input = $state('');
  let ragOn = $state(true);
  let ragScope = $state('all');
  let streaming = $state(false);
  /** @type {HTMLDivElement} */
  let bodyEl;

  const SCOPES = { all: 'transcript', transcript: 'selection', selection: 'all' };
  function cycleScope() { ragScope = SCOPES[ragScope]; }

  function scrollBottom() {
    tick().then(() => {
      if (bodyEl) bodyEl.scrollTop = bodyEl.scrollHeight;
    });
  }

  async function send() {
    const text = input.trim();
    if (!text || streaming) return;

    input = '';
    streaming = true;

    const ts = new Date().toLocaleTimeString('en', { hour: '2-digit', minute: '2-digit' });
    const uid = `u_${Date.now()}`;

    app.pushMessage({ role: 'user', content: text, id: uid, ts });
    // Placeholder for the assistant turn — MessageStream will fill it in
    const aid = `a_${Date.now()}`;
    app.pushMessage({ role: 'assistant', content: '', id: aid, ts, streaming: true });

    scrollBottom();
  }

  function onStreamDone(citeIds) {
    streaming = false;
    app.sealLastMessage(citeIds);
    scrollBottom();
  }

  function onKeydown(e) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      send();
    }
  }

  function newThread() {
    app.clearMessages();
    streaming = false;
  }

  // Build the message list to pass to MessageStream for the current streaming turn
  let streamMessages = $derived.by(() => {
    const msgs = app.messages;
    if (!msgs.length) return [];
    // Find the last assistant placeholder and pass everything before it
    const lastAssistIdx = msgs.map((m) => m.role).lastIndexOf('assistant');
    if (lastAssistIdx <= 0) return [];
    return msgs
      .slice(0, lastAssistIdx)
      .filter((m) => !m.streaming)
      .map((m) => ({ role: m.role, content: m.content }));
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
        {:else if msg.streaming && streaming}
          <Message role="assistant" who="QS" ts={msg.ts} model={model.name}>
            <MessageStream
              messages={streamMessages}
              model={model.name}
              rag={{ on: ragOn, scope: ragScope }}
              onDone={onStreamDone}
            />
          </Message>
        {:else if !msg.streaming}
          <Message role="assistant" who="QS" ts={msg.ts} model={model.name}>
            <p>{msg.content || '—'}</p>
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
        disabled={streaming}
      ></textarea>
      <div class="row">
        <div class="slash">
          <span class="cmd">/summarize</span>
          <span class="cmd">/find-themes</span>
          <span class="cmd">/cite</span>
          <span class="cmd">/contradict</span>
        </div>
        <button class="send" onclick={send} disabled={streaming}>
          {streaming ? 'streaming…' : 'send'} <span class="k">⌘↵</span>
        </button>
      </div>
    </div>
  </div>
</div>
