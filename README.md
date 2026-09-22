# AI Shorts Video - Cloudflare Worker V3

Cloudflare-first FastAPI backend for the Miko AI Shorts project.

## Important architecture decision

The Story Engine does NOT read JSON files at Worker startup.

The Miko Character Bible, Story Bible, and World Bible are embedded in:

`src/engines/bibles.py`

This avoids the filesystem/package-data problem encountered with Python Workers/Pyodide.

## Structure

```text
ai-shorts-video/
├── src/
│   ├── main.py
│   └── engines/
│       ├── __init__.py
│       ├── bibles.py
│       └── story_engine.py
├── pyproject.toml
├── wrangler.jsonc
└── .gitignore
```

There is intentionally NO requirements.txt.

## Cloudflare Build settings

Build command:

leave blank

Deploy command:

```text
uv run pywrangler deploy
```

## Endpoints

- GET /
- GET /health
- GET /bibles
- GET /story/options
- POST /story/generate
- GET /pipeline/status
- GET /docs

## Why this is Cloudflare-safe

The Worker uses:
- FastAPI
- Pydantic
- standard Python modules only for the Story Engine
- workers ASGI entrypoint
- no filesystem access
- no local database
- no ffmpeg
- no local video processing
- no JSON resource loading

Cloudflare/Pywrangler bundles Python dependencies from pyproject.toml.
