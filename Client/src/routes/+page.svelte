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

  let chatOutput = $state("Chat Here");

  let chatIsGenerating = $state(false)

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


  async function processPrompt() {

    chatIsGenerating = true;

        const response = await fetch(`http://127.0.0.1:8000/askForRecipe?prompt=${encodeURIComponent(input_prompt)}`, {
      method: 'GET',
      headers: {
        'accept': 'application/json',
      }
    });

    const data = await response.json()
    console.log(data.result)

    chatOutput = data.result

    chatIsGenerating = false;

    return
  }

</script>
<div class="grid h-56 grid-cols-1 content-start gap-4 ml-20 mr-20 ...">

  

<div>

</div>

<h1 class="text-center ml-1 text-3xl font-bold">QSTAT</h1>

<label for="many" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-full">Upload Audio File</label>
<input bind:files accept="audio/mpeg, audio/wav" id="many" multiple type="file"/>
<button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-full" onclick={UploadFile}>Transcribe</button>

{#if files}
	<h2>Selected files:</h2>
	{#each Array.from(files) as file}
		<p>{file.name} ({file.size} bytes)</p>
	{/each}
{/if}


{#if chatIsGenerating}
  <h1>LOADING CHAT RESPONSE . . .</h1>
{/if}
<input bind:value={input_prompt} placeholder="Frage nach Rezepten" />
<button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-full" onclick={processPrompt}>Send Prompt</button>
<div class="prose">{@html marked(chatOutput)}</div>

<!--<p class="border-2 p-5 m-5">Transcription Output: {transcriptionResponse?.transcription?.text}</p> -->

<h1>Transcription</h1>
<ul class="p-5">
  {#each transcriptionResponse?.transcription?.segments as seg}
    <li>
      <strong>{seg.start_formatted}</strong> → <strong>{seg.end_formatted}:</strong>
      {seg.text}
    </li>
  {/each}
</ul>

</div>

