docker compose -f Chroma/compose.yml up -d

uvicorn API.server:app --reload --port 8001