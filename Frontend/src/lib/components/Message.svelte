<script>
  /** @type {{ role: 'user' | 'assistant', who: string, ts: string, model?: string, children?: import('svelte').Snippet }} */
  let { role, who, ts, model = undefined, children } = $props();
</script>

<div class="msg {role}">
  <div class="role">
    <span class="av">{who}</span>
    <span>{role === 'user' ? 'you' : model || 'assistant'}</span>
    <span class="ts">{ts}</span>
  </div>
  <div class="body">
    {@render children?.()}
  </div>
</div>
