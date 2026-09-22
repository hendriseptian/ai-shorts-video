from __future__ import annotations

from typing import Any, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from engines.story_engine import StoryEngine, StoryEngineError
from engines.image_prompt_engine import ImagePromptEngine, ImagePromptEngineError
from engines.image_generation_engine import (
    ImageGenerationEngine,
    ImageGenerationError,
)


APP_NAME = "AI Shorts Video API"
APP_VERSION = "0.5.1"

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

story_engine = StoryEngine()
image_prompt_engine = ImagePromptEngine()
image_generation_engine = ImageGenerationEngine()


class StoryGenerateRequest(BaseModel):
    category: Optional[str] = None
    core_value: Optional[str] = None
    location: Optional[str] = None
    supporting_character: Optional[str] = None
    main_object: Optional[str] = None
    duration: int = Field(default=60, ge=10, le=180)
    language: str = Field(default="id", min_length=2, max_length=5)
    episode_id: Optional[str] = None


class ImagePromptRequest(BaseModel):
    story: dict[str, Any]
    episode_id: Optional[str] = None
    language: str = Field(default="id", min_length=2, max_length=5)


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12000)
    negative_prompt: str = Field(default="", max_length=12000)
    scene_number: int = Field(default=1, ge=1, le=99)
    episode_id: Optional[str] = None
    steps: int = Field(default=4, ge=1, le=8)
    seed: Optional[int] = None
    aspect_ratio: str = Field(default="9:16", min_length=3, max_length=10)
    resolution: str = Field(default="1080x1920", min_length=5, max_length=20)


@app.get("/")
async def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "online",
        "story_engine": "ready",
        "image_prompt_engine": image_prompt_engine.VERSION,
        "image_generation_engine": image_generation_engine.VERSION,
        "image_provider": image_generation_engine.provider,
        "image_model": image_generation_engine.model,
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "story_engine": "ready",
        "image_prompt_engine": "ready",
        "image_generation_engine": "ready",
        "image_provider": image_generation_engine.provider,
        "image_model": image_generation_engine.model,
        "platform": "cloudflare-python-workers",
    }


@app.get("/bibles")
async def bibles():
    return story_engine.get_bibles()


@app.get("/story/options")
async def story_options():
    return story_engine.get_options()


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
            "data": story,
        }
    except StoryEngineError as exc:
        return {
            "success": False,
            "error": str(exc),
        }


@app.post("/story/image-prompts")
async def generate_image_prompts(request: ImagePromptRequest):
    try:
        # ImagePromptEngine derives episode_id and language directly
        # from the story payload. Keep this call compatible with the
        # Cloudflare-safe engine signature.
        result = image_prompt_engine.generate_for_story(
            story=request.story,
        )
        return {
            "success": True,
            **result,
        }
    except ImagePromptEngineError as exc:
        return {
            "success": False,
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Unexpected image prompt error: {exc}",
        }


@app.post("/images/generate")
async def generate_image(request: ImageGenerateRequest):
    try:
        result = await image_generation_engine.generate(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            steps=request.steps,
            seed=request.seed,
            resolution=request.resolution,
        )

        return {
            "success": True,
            "scene_number": request.scene_number,
            "episode_id": request.episode_id,
            "aspect_ratio": request.aspect_ratio,
            "resolution": request.resolution,
            **result,
        }

    except ImageGenerationError as exc:
        return {
            "success": False,
            "scene_number": request.scene_number,
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "success": False,
            "scene_number": request.scene_number,
            "error": f"Unexpected image generation error: {exc}",
        }


@app.get("/pipeline/status")
async def pipeline_status():
    return {
        "story_engine": {
            "status": "READY",
            "version": getattr(story_engine, "VERSION", "1.0.0"),
        },
        "image_prompt_engine": {
            "status": "READY",
            "version": image_prompt_engine.VERSION,
        },
        "image_generation_engine": {
            "status": "READY",
            "version": image_generation_engine.VERSION,
            "provider": image_generation_engine.provider,
            "model": image_generation_engine.model,
        },
        "next_stage": "voice_generation",
    }


from workers import asgi

Default = asgi.entrypoint(app)
