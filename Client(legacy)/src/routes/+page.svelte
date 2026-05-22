<script lang="ts">
    import { marked } from 'marked'

  let files = $state<FileList | undefined>();

  let transcriptionResponse = $state<{
     transcription?: {
      text: string;

     segments?: {
      start_formatted: string;
      end_formatted: string;
      text: string;
     }[];
    
     }
    } | null>(null);

  let input_prompt = $state("");
  let enableThinking = $state(false)
  let output = $state("");

  
  const llmModes = ["recipes", "codebook"]
  let selectedMode = $state(llmModes[0])

    async function send() {
    output = '';

    const res = await fetch('http://127.0.0.1:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages: [{ role: 'user', content: input_prompt }],
        thinking : enableThinking,
        mode : selectedMode
      })
    });

    const reader = res.body?.getReader();
    const decoder = new TextDecoder();

    let buffer = '';

    while (reader) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;

        const data = line.slice(6);

        if (data === '[DONE]') return;

        const json = JSON.parse(data);
        output += json.choices[0].delta.content ?? '';
      }
    }
  }

  $effect(() => {
    if(files) {
      console.log(files)
      for (const file of files) {
          console.log(`${file.name}: ${file.size} bytes`);
      }
    }
  });


  async function UploadFile() {
    
    if (!files || files.length === 0) {
    console.log('No file selected');
    return;
    }

    const formData = new FormData();
    formData.append("file", files[0]);

    const response = await fetch('http://127.0.0.1:8000/uploadfile', {
      method: 'POST',
      body: formData  
      });

    const data = await response.json()
    transcriptionResponse = data;
    }


</script>


<h1 class="text-center ml-1 text-3xl font-bold mb-20">QSTAT</h1>

<div class="grid h-56 grid-cols-2 content-start gap-4 ml-20 mr-20 ...">
    <div class="col-1">
      <label for="many" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-full">Upload Audio File</label>
      <input bind:files accept="audio/mpeg, audio/wav" id="many" multiple type="file"/>
      <button class="mt-5 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-full" onclick={UploadFile}>Transcribe</button>
      <p class="border-2 p-5 m-5">Transcription Output: {transcriptionResponse?.transcription?.text}</p>

      {#if files}
        <h2>Selected files:</h2>
        {#each Array.from(files) as file}
          <p>{file.name} ({file.size} bytes)</p>
        {/each}
      {/if}

      <h1>Transcription Output:</h1>
      <ul class="p-5">
        {#each transcriptionResponse?.transcription?.segments as seg}
          <li>
            <strong>{seg.start_formatted}</strong> → <strong>{seg.end_formatted}:</strong>
            {seg.text}
          </li>
        {/each}
      </ul>
    </div>

    <div class="grid col-2">
      <textarea class="border-2 w-100 h-20 row-1 " placeholder="Frage nach Rezepten" bind:value={input_prompt}></textarea>
      <button class="mt-2 w-50  row-2 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-full" onclick={send}>Send</button>
      <label>
      <input class="row-3" type="checkbox" bind:checked={enableThinking}/>
      Enable Thinking?
      </label>
      <p>Mode:</p>
      <select class="row-4 border-2" bind:value={selectedMode}>
        {#each llmModes as mode}
          <option value={mode}>
            {mode}
          </option>
        {/each}
      </select>

      <div class="row-5 prose">{@html marked(output)}</div>
    </div>
</div>

