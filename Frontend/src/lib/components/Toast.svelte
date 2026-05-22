<script>
  import { app } from '$lib/state.svelte.js';
</script>

{#if app.toasts.length}
  <div class="toast-stack" aria-live="polite">
    {#each app.toasts as t (t.id)}
      <!-- svelte-ignore a11y_no_static_element_interactions -->
      <div
        class="toast {t.kind}"
        onclick={() => app.dismissToast(t.id)}
        role="alert"
      >
        {t.msg}
      </div>
    {/each}
  </div>
{/if}

<style>
  .toast-stack {
    position: fixed;
    bottom: 20px;
    left: 50%;
    translate: -50% 0;
    display: flex;
    flex-direction: column;
    gap: 6px;
    z-index: 999;
    pointer-events: none;
  }
  .toast {
    pointer-events: all;
    padding: 8px 14px;
    border-radius: 6px;
    font-family: var(--f-mono);
    font-size: 11px;
    cursor: pointer;
    animation: toast-in 0.18s ease;
  }
  .toast.error {
    background: oklch(0.25 0.06 25);
    color: oklch(0.85 0.08 30);
    border: 1px solid oklch(0.35 0.1 25);
  }
  .toast.info {
    background: var(--bg-elev);
    color: var(--ink-2);
    border: 1px solid var(--hair);
  }
  @keyframes toast-in {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }
</style>
