<script>
  import TopBar from '$lib/components/TopBar.svelte';
  import ContextPane from '$lib/components/ContextPane.svelte';
  import TranscriptPane from '$lib/components/TranscriptPane.svelte';
  import CodebookPane from '$lib/components/CodebookPane.svelte';
  import ChatPane from '$lib/components/ChatPane.svelte';
  import Tweaks from '$lib/components/Tweaks.svelte';
  import LogWindow from '$lib/components/LogWindow.svelte';
  import Toast from '$lib/components/Toast.svelte';
  import { app } from '$lib/state.svelte.js';
  import { PROJECT } from '$lib/data.js';
</script>

<svelte:head>
  <title>QualScope — qualitative data analysis</title>
</svelte:head>

<TopBar project={PROJECT} />

<div class="app">
  <ContextPane />
  <div class="divider"></div>

  <TranscriptPane />

  <div class="divider"></div>
  <CodebookPane />

  <div class="divider"></div>
  <ChatPane />
</div>

<Tweaks />
<LogWindow />
<Toast />
