from __future__ import annotations

from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from engines.story_engine import StoryEngine, StoryEngineError


APP_NAME = "AI Shorts Video API"
APP_VERSION = "0.2.0"

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Cloudflare Python Worker backend for the Miko AI Shorts pipeline.",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Important: this is now safe at Worker startup because no filesystem
# or external resource loading is performed by StoryEngine.
story_engine = StoryEngine()


class StoryGenerateRequest(BaseModel):
    category: Optional[str] = None
    core_value: Optional[str] = None
    location: Optional[str] = None
    supporting_character: Optional[str] = None
    main_object: Optional[str] = None
    duration: int = Field(default=60, ge=10, le=180)
    language: str = Field(default="id", min_length=2, max_length=5)
    episode_id: Optional[str] = None


@app.get("/")
async def root():
    return {
        "status": "online",
        "application": APP_NAME,
        "version": APP_VERSION,
        "platform": "cloudflare-python-workers",
        "engine": "story-engine",
        "bible_storage": "embedded-python",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "story_engine": "ready",
        "platform": "cloudflare-python-workers",
    }


@app.get("/bibles")
async def bibles():
    return {
        "character_bible": True,
        "story_bible": True,
        "world_bible": True,
        "storage": "embedded-python",
    }


@app.get("/story/options")
async def story_options():
    return {
        "categories": story_engine.story_bible["categories"],
        "core_values": story_engine.story_bible["core_values"],
        "locations": [
            {
                "id": item["id"],
                "name": item["name"],
            }
            for item in story_engine.world_bible["locations"]
        ],
        "supporting_characters": [
            {
                "id": item["id"],
                "name": item["name"],
                "species": item["species"],
            }
            for item in story_engine.character_bible[
                "supporting_characters"
            ]
        ],
        "languages": ["id", "en"],
        "durations": [30, 45, 60, 90],
    }


@app.post("/story/generate")
async def generate_story(request: StoryGenerateRequest):
    try:
        story = story_engine.generate_story(
            category=request.category,
            core_value=request.core_value,
            location=request.location,
            supporting_character=request.supporting_character,
            main_object=request.main_object,
            duration=request.duration,
            language=request.language,
            episode_id=request.episode_id,
        )

        return {
            "success": True,
            "engine": "story-engine",
            "version": APP_VERSION,
            "data": story,
        }

    except StoryEngineError as exc:
        return {
            "success": False,
            "engine": "story-engine",
            "error": str(exc),
        }


@app.get("/pipeline/status")
async def pipeline_status():
    return {
        "story_engine": "READY",
        "scene_engine": "PLANNED",
        "video_engine": "PLANNED",
        "voice_engine": "PLANNED",
        "edit_engine": "PLANNED",
        "qc_engine": "PLANNED",
        "youtube_engine": "PLANNED",
        "automation_engine": "PLANNED",
    }


from workers import asgi

Default = asgi.entrypoint(app)
