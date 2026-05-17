FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

WORKDIR /app

RUN apt-get update \
    && apt-get install -y ffmpeg

COPY requirements.txt .

RUN pip install  -r requirements.txt

#--no-cache-dir production argument!!

COPY . .

EXPOSE 8000

CMD ["uvicorn", "API.server:app", "--host", "0.0.0.0", "--port", "8000"]