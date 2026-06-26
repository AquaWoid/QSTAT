
# QSTAT

Open Source Speech Transcription and Analysis Software.

---
## Requirements

#### Hardware 

|     | Minimum         | Recommended     | Test System          | CPU Only Test System |
| --- | --------------- | --------------- | -------------------- | -------------------- |
| CPU | i5 10xxx 4 Core | i7 13xxx 8 core | i9 12900KF 16 Core   | i5 1135G7 4 Core     |
| RAM | 8 GB            | 16 GB           | 32 GB                | 16 GB                |
| GPU | GTX 1080 8GB    | RTX 5070 12 GB  | RTX 4080 Super 16 GB | -                    |
#### OS
- Windows 11
	- WSL: https://learn.microsoft.com/en-us/windows/wsl/install
	- Docker Desktop: https://www.docker.com/products/docker-desktop/
- MacOS
	- Docker Desktop: https://www.docker.com/products/docker-desktop/
- Linux (Tested on Ubuntu 24.04)
	- Docker: https://docs.docker.com/engine/install/ubuntu/

#### File Size (including Models and ML Frameworks)
- GPU Version: ~20GB 
- CPU Version: ~12GB

--- 
## Installation
#### Docker Compose

#### GPU Version (Recommended)
From the main directory open a terminal:
1. Clone this repo with `git clone https://github.com/AquaWoid/QSTAT.git`
2. Move to the main directory `cd QSTAT`
3. Create a .env files from the template with ```cp .env.example .env```
	1. ```HUGGING_FACE_HUB_TOKEN``` needed if you want faster Model downloads. 
		1. Refer to: https://huggingface.co/docs/hub/en/security-tokens
	2. ```OPENROUTER_KEY``` enables the use of cloud LLMs
		1. Refer to: https://openrouter.ai/workspaces/default/keys
	3. ```MODEL_NAME``` Identifier of the local LLM
		1. Default model (Qwen3-4b-AWQ)  works with as low as 2GB VRAM. Memory cost scales with context window size. 
	4. ```CONTEXT_WINDOW_LEN``` Context window of the local LLM. Adjust according to your hardware
		1. You can check VRAM requirements estimations at: https://apxml.com/models/
4. Build the docker setup once with `docker compose build`
	1. Building the image for the first time takes around 5-10 Minutes depending on hardware and download speed. Python's ML stack
5. Run the containers with `docker compose up -d`
	1. First deployment needs to download the vLLM Image (9GB) which adds another 2-10 minutes depending on download speed.
6. Check if everything's working by visiting `app.localhost` and `api.localhost/docs` 
7. Check vLLM's logs if everything is working. This can either be done in Docker Desktop or with `docker compose logs -f vllm`. On success the last line should display `Application startup complete.` 

#### CPU Version 

##### Disclaimer
The Software and it's main components are heavily optimized for GPU-use. They will work on CPU+RAM but with very limited performance. Expect vLLM to take quite a long time to load and initialize the model. If your RAM is too low to load the model you have to adjust the flag `--gpu-memory-utilization` in `docker-compose-cpu.yml`. Despite the name this flags is used for RAM utilization in the CPU version of vLLM. 

1. Follow steps 1-3 from the GPU Setup
2. Build with `docker compose -f docker-compose-cpu.yml`
3. Run the container with `docker compose -f docker-compose-cpu.yml up -d`
4. Wait for packages and models to be installed (10-20 Minutes)
5. Check if everything's working by visiting `app.localhost` and `api.localhost/docs` 
6. Check vLLMs logs with `docker compose logs -f vllm` or directly in Docker Desktop. 
	1. Insufficient hardware can make issues. If the logs say something like `ValueError: Available memory on node 0 on startup is less than desired CPU memory utilization` you have do lower the utilization like already mentioned in the above disclaimer and restart the vllm container with ``docker compose -f docker-compose-cpu.yml up -d vllm`

--- 
#### Native Install

If you don't want to use docker or for development you can run all services natively on any OS too

From the main directory open one terminal window for **each** service:
1. Client:
	1. `cd Frontend`
	2. `npm install`
	3. `npm run dev` 
2. Backend
	1. `cd Backend`
	2. `python3 -m venv .venv`
	3. `source venv/bin/activate`
	4. `pip install -r requirements.txt`
	5. `uvicorn API.server:app --reload --port 8000`
3. vLLM
	1. `mkdir vllm`
	2. `cd vllm`
	3. `python3 -m venv .venv`
	4. `source venv/bin/activate`
	5. `pip install vllm` 
	6. ```sh
	    python -m vllm.entrypoints.openai.api_server \
			  --model Qwen/Qwen3-4B-AWQ \
			  --max-model-len 4096 \
			  --gpu-memory-utilization 0.85
		```
---

# Usage

## Context Panel

- Model
	- Select your desired transcription model
- Research Question
	- Define a research question that will be used for deductive category building
- Model Cache
	- Download your desired transcription model.
	- At least one has to be downloaded to upload audio files
	- Qwen3 ASR is GPU only currently. If you're running the CPU version please use Whisper.
- Document Section
	- Audio 
		- Transcribed Audio Files. Click to open the transcript in the editor window
	- Documents
		- PDF Only for now. Click to open PDF in the editor window
## Editor Window

- View Transcriptions and edit transcriptions
- View PDF documents using the browser's native pdf viewer

## Codebook Panel

- Add code categories manually using the + icon.
- Once a category is created, hover over it, press the three dots and either add a code or delete the category group.
- Codes can be dragged onto transcript segments to apply them 
- Generate
	- Inductive codebook generation
	- Needs an open transcript to work
	- Might need some time depending on the model
		- Cloud will usually take longer than the local model
- Deductive
	- Deductive codebook generation
	- Needs a defined research question to work 
	- Currently still in prototyping phase
		- Generates codes based on ten "relevant" papers taken from the models own data based on the research question

## Chat Panel

- Model Selection
	- Select one of the provided models
	- For now it is advised to use the provided local model 
		- Qwen3-4B-AWQ for the GPU version
		- Qwen3-0.6B for the CPU version
	- This means it is also advised to keep the models in the projects .env file like they are since the logic to dynamically detect the loaded model is not yet fully implemented.
- Copy Thread Button
	- Copies the complete chat as Markdown
- + Button
	- Opens a new chat and discards the previous one
- @docs Button
	- Toggles the RAG system
- General
	- Conversation context consists of all of the current chat outputs and RAG retrieved text chunks based on the input / question
	- For testing the RAG System, try to ask the model about transcripts or papers you've provided
	- When using RAG the model is tasked to only include facts from the provided sources

## Top Bar 

- Stats
	- Status
		- Shows if a file is processing
	- Files Codes and Transcripts
		- Shows the count of those
- Sun Symbol 
	- Tweaks menu 
	- Adjust Application style and spacings to your liking
	- Chat window can be toggled for better visual clarity when working with codes
