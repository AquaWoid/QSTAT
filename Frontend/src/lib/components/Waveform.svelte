<script>
  /** @type {{ progress?: number }} */
  let { progress = 0.42 } = $props();

  // Deterministic pseudo-waveform — looks like speech envelope.
  const bars = (() => {
    const N = 220;
    const out = [];
    let seed = 137;
    const rng = () => (seed = (seed * 9301 + 49297) % 233280) / 233280;
    for (let i = 0; i < N; i++) {
      const t = i / N;
      const env =
        0.35 +
        0.3 * Math.sin(t * Math.PI * 2.4 + 0.5) +
        0.22 * Math.sin(t * Math.PI * 9 + 1.3) +
        0.1 * (rng() - 0.5) * 2;
      out.push(Math.max(0.08, Math.min(1, env)));
    }
    return out;
  })();
</script>

<div class="wave-wrap" style="position:relative; width:100%; height:100%;">
  <svg viewBox="0 0 {bars.length * 3} 40" preserveAspectRatio="none">
    {#each bars as h, i}
      {@const played = i / bars.length <= progress}
      {@const half = h * 17}
      <rect
        x={i * 3 + 0.5}
        y={20 - half}
        width="1.5"
        height={half * 2}
        fill={played ? 'currentColor' : 'var(--hair-2)'}
        opacity={played ? 0.7 : 0.55}
      />
    {/each}
  </svg>
  <div class="scrubber" style="left: {progress * 100}%"></div>
</div>
