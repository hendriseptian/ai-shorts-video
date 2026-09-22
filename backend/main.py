from pathlib import Path
import zipfile

base = Path("/mnt/data/main-py-v1/backend")
base.mkdir(parents=True, exist_ok=True)

main_py = r'''"""
AI Shorts Video - Backend API V1

Main API entry point for the AI Shorts Video production system.

Current pipeline:
    API
      ↓
    Story Engine
      ↓
    Story JSON

Planned pipeline:
    Story → Scene → Video → Voice → Edit → QC → YouTube
"""

from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from engines.story_engine import (
    StoryEngine,
    StoryEngineError,
)


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

APP_NAME = "AI Shorts Video API"
APP_VERSION = "0.1.0"


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("ai-shorts-video")


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=(
        "Backend API for the Miko AI Shorts Video production system."
    ),
)


# ============================================================
# CORS
# ============================================================

# Development configuration.
# Production domains should be restricted later.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STORY ENGINE
# ============================================================

story_engine = StoryEngine()


# ============================================================
# REQUEST MODELS
# ============================================================

class StoryGenerateRequest(BaseModel):
    """
    Request body for Story Engine.

    Any field except language can be omitted.
    When omitted, Story Engine selects a value automatically.
    """

    category: Optional[str] = Field(
        default=None,
        description="Story category, for example ADVENTURE.",
    )

    core_value: Optional[str] = Field(
        default=None,
        description="Core value, for example COURAGE.",
    )

    location: Optional[str] = Field(
        default=None,
        description="Miko world location.",
    )

    supporting_character: Optional[str] = Field(
        default=None,
        description="Optional supporting character.",
    )

    main_object: Optional[str] = Field(
        default=None,
        description="Main story object.",
    )

    duration: Optional[int] = Field(
        default=60,
        ge=10,
        le=180,
        description="Target story duration in seconds.",
    )

    language: str = Field(
        default="id",
        description="Story language.",
    )

    episode_id: Optional[str] = Field(
        default=None,
        description="Optional custom episode ID.",
    )


# ============================================================
# RESPONSE MODELS
# ============================================================

class APIStatusResponse(BaseModel):
    status: str
    application: str
    version: str


class HealthResponse(BaseModel):
    status: str
    story_engine: str


class BibleResponse(BaseModel):
    character_bible: str
    story_bible: str
    world_bible: str


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get(
    "/",
    response_model=APIStatusResponse,
    tags=["System"],
)
def root() -> APIStatusResponse:
    """
    Basic API status.
    """

    return APIStatusResponse(
        status="online",
        application=APP_NAME,
        version=APP_VERSION,
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
)
def health() -> HealthResponse:
    """
    Health check for the backend and Story Engine.
    """

    try:
        story_engine.bibles

        return HealthResponse(
            status="healthy",
            story_engine="ready",
        )

    except Exception as exc:
        logger.exception("Health check failed: %s", exc)

        return HealthResponse(
            status="degraded",
            story_engine="error",
        )


# ============================================================
# BIBLE STATUS
# ============================================================

@app.get(
    "/bibles",
    response_model=BibleResponse,
    tags=["System"],
)
def bibles() -> BibleResponse:
    """
    Check whether the three Miko Bible files are loaded.
    """

    try:
        character = story_engine.character_bible
        story = story_engine.story_bible
        world = story_engine.world_bible

        return BibleResponse(
            character_bible=(
                "loaded"
                if character
                else "missing"
            ),
            story_bible=(
                "loaded"
                if story
                else "missing"
            ),
            world_bible=(
                "loaded"
                if world
                else "missing"
            ),
        )

    except Exception as exc:
        logger.exception(
            "Bible status check failed: %s",
            exc,
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to load Miko Bible files.",
        ) from exc


# ============================================================
# STORY GENERATION
# ============================================================

@app.post(
    "/story/generate",
    tags=["Story Engine"],
)
def generate_story(
    request: StoryGenerateRequest,
):
    """
    Generate one complete Miko story.

    Example request:

    {
        "category": "ADVENTURE",
        "core_value": "COURAGE",
        "location": "SUNNY_FOREST",
        "supporting_character": "KIKI",
        "main_object": "RAINBOW",
        "duration": 60,
        "language": "id"
    }
    """

    logger.info(
        "Generating story | category=%s | value=%s | location=%s",
        request.category,
        request.core_value,
        request.location,
    )

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
            "engine": "STORY_ENGINE",
            "version": "1.0",
            "data": story,
        }

    except StoryEngineError as exc:
        logger.warning(
            "Story generation rejected: %s",
            exc,
        )

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.exception(
            "Unexpected story generation error."
        )

        raise HTTPException(
            status_code=500,
            detail="Unexpected error while generating story.",
        ) from exc


# ============================================================
# STORY ENGINE OPTIONS
# ============================================================

@app.get(
    "/story/options",
    tags=["Story Engine"],
)
def story_options():
    """
    Return available Story Engine options.

    This endpoint will later be used by the dashboard
    dropdown menus.
    """

    try:
        categories = story_engine.story_bible.get(
            "categories",
            [],
        )

        core_values = story_engine.story_bible.get(
            "core_values",
            [],
        )

        locations = [
            {
                "id": item.get("id"),
                "name": item.get("name"),
            }
            for item in story_engine.world_bible.get(
                "locations",
                [],
            )
        ]

        supporting_characters = [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "species": item.get("species"),
            }
            for item in story_engine.world_bible.get(
                "supporting_characters",
                [],
            )
        ]

        return {
            "success": True,
            "data": {
                "categories": categories,
                "core_values": core_values,
                "locations": locations,
                "supporting_characters": supporting_characters,
                "languages": ["id", "en"],
                "durations": [30, 45, 60, 90],
            },
        }

    except Exception as exc:
        logger.exception(
            "Unable to load story options."
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to load Story Engine options.",
        ) from exc


# ============================================================
# PIPELINE STATUS
# ============================================================

@app.get(
    "/pipeline/status",
    tags=["Pipeline"],
)
def pipeline_status():
    """
    Current production pipeline status.

    Only Story Engine is active in V1.
    Other engines are placeholders for future versions.
    """

    return {
        "success": True,
        "pipeline": [
            {
                "engine": "STORY_ENGINE",
                "status": "READY",
                "version": "1.0",
            },
            {
                "engine": "SCENE_ENGINE",
                "status": "PLANNED",
                "version": None,
            },
            {
                "engine": "VIDEO_ENGINE",
                "status": "PLANNED",
                "version": None,
            },
            {
                "engine": "VOICE_ENGINE",
                "status": "PLANNED",
                "version": None,
            },
            {
                "engine": "EDIT_ENGINE",
                "status": "PLANNED",
                "version": None,
            },
            {
                "engine": "QC_ENGINE",
                "status": "PLANNED",
                "version": None,
            },
            {
                "engine": "YOUTUBE_ENGINE",
                "status": "PLANNED",
                "version": None,
            },
            {
                "engine": "AUTOMATION_ENGINE",
                "status": "PLANNED",
                "version": None,
            },
        ],
    }


# ============================================================
# DEVELOPMENT SERVER
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
'''

(base / "main.py").write_text(main_py, encoding="utf-8")

zip_path = Path("/mnt/data/backend-main-v1.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    z.write(base / "main.py", arcname="backend/main.py")

print(zip_path)
