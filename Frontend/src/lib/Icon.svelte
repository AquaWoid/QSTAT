<!--
  Minimal stroke-icon set, 13px default, in IBM/Phosphor school.
  Usage: <Icon name="search" />
-->
<script>
  /** @type {{ name: string, size?: number, fill?: boolean, class?: string }} */
  let { name, size = 13, fill = false, class: klass = '' } = $props();
</script>

<svg
  class="ic {klass}"
  width={size}
  height={size}
  viewBox="0 0 16 16"
  fill={fill ? 'currentColor' : 'none'}
  stroke={fill ? 'none' : 'currentColor'}
  stroke-width="1.5"
  stroke-linecap="round"
  stroke-linejoin="round"
>
  {#if name === 'search'}
    <circle cx="7" cy="7" r="4.5" /><path d="M10.5 10.5 14 14" />
  {:else if name === 'plus'}
    <path d="M8 3v10M3 8h10" />
  {:else if name === 'filter'}
    <path d="M2 4h12M4 8h8M6 12h4" />
  {:else if name === 'sort'}
    <path d="M4 3v10M2 11l2 2 2-2M12 13V3M14 5l-2-2-2 2" />
  {:else if name === 'more'}
    <circle cx="4" cy="8" r="1.2" fill="currentColor" stroke="none" />
    <circle cx="8" cy="8" r="1.2" fill="currentColor" stroke="none" />
    <circle cx="12" cy="8" r="1.2" fill="currentColor" stroke="none" />
  {:else if name === 'chev-down'}
    <path d="M3.5 6 8 10.5 12.5 6" />
  {:else if name === 'chev-right'}
    <path d="M6 3.5 10.5 8 6 12.5" />
  {:else if name === 'play'}
    <path d="M5 3.5v9l8-4.5z" fill="currentColor" stroke="none" />
  {:else if name === 'pause'}
    <rect x="4.5" y="3.5" width="2.5" height="9" rx="0.5" fill="currentColor" stroke="none" />
    <rect x="9" y="3.5" width="2.5" height="9" rx="0.5" fill="currentColor" stroke="none" />
  {:else if name === 'send'}
    <path d="M2.5 8h10M9 4.5 12.5 8 9 11.5" />
  {:else if name === 'upload'}
    <path d="M8 11V3M5 6l3-3 3 3M3 12v1.5h10V12" />
  {:else if name === 'copy'}
    <rect x="5" y="5" width="8" height="8" rx="1" /><path d="M3 11V3.5h8" />
  {:else if name === 'refresh'}
    <path d="M3 8a5 5 0 0 1 8.5-3.5L13 6M13 3v3h-3M13 8a5 5 0 0 1-8.5 3.5L3 10M3 13v-3h3" />
  {:else if name === 'settings'}
    <circle cx="8" cy="8" r="2" />
    <path d="M8 1v2M8 13v2M1 8h2M13 8h2M3 3l1.4 1.4M11.6 11.6 13 13M3 13l1.4-1.4M11.6 4.4 13 3" />
  {:else if name === 'cite'}
    <path d="M3 4.5h4v4H3zM3 8.5c0 2 1 3 2.5 3.5M9 4.5h4v4H9zM9 8.5c0 2 1 3 2.5 3.5" />
  {:else if name === 'info'}
    <circle cx="8" cy="8" r="6" />
    <circle cx="8" cy="5.5" r="0.8" fill="currentColor" stroke="none" />
    <path d="M8 8v3.5" stroke-width="1.75" />
  {:else if name === 'trash'}
    <path d="M3 5h10M6 5V3.5h4V5M4.5 5l.75 8h5.5l.75-8" />
  {:else if name === 'console'}
    <rect x="2" y="3" width="12" height="10" rx="1" />
    <path d="M4.5 6.5 7 8.5 4.5 10.5" />
    <path d="M8 10.5h3.5" />
  {/if}
</svg>
