from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from engines.story_engine import StoryEngine, StoryEngineError
from engines.image_prompt_engine import ImagePromptEngine, ImagePromptEngineError
from engines.image_generation_engine import (
    ImageGenerationEngine,
    ImageGenerationEngineError,
)
from engines.video_generation_engine import (
    VideoGenerationEngine,
    VideoGenerationError,
    VideoGenerationInputError,
    VideoGenerationConfigurationError,
)


APP_NAME = "AI Shorts Video API"
APP_VERSION = "0.5.0"

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
    story: dict
    episode_id: Optional[str] = None
    language: str = Field(default="id", min_length=2, max_length=5)


class ImageGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    reference_image: str
    width: int = Field(default=576, ge=256, le=1920)
    height: int = Field(default=1024, ge=256, le=1920)
    seed: Optional[int] = None
    scene_number: Optional[int] = None


class VideoGenerateRequest(BaseModel):
    image: str
    motion_prompt: str = ""
    duration: int = Field(default=5, ge=1, le=20)
    resolution: str = Field(default="720p")
    fps: int = Field(default=24)
    draft: bool = Field(default=True)
    seed: Optional[int] = None
    scene_number: Optional[int] = None


@app.get("/")
async def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "story_engine": "ready",
        "image_prompt_engine": "ready",
        "image_generation_engine": "ready",
        "video_generation_engine": "ready",
        "video_provider": "cloudflare-workers-ai",
        "video_model": "pruna/p-video",
        "image_provider": "cloudflare-workers-ai",
        "image_model": "@cf/black-forest-labs/flux-2-klein-4b",
        "character_identity": "MIKO_CAT",
        "character_reference": "required",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "story_engine": "ready",
        "image_prompt_engine": "ready",
        "image_generation_engine": "ready",
        "video_generation_engine": "ready",
        "video_provider": "cloudflare-workers-ai",
        "video_model": "pruna/p-video",
        "image_provider": "cloudflare-workers-ai",
        "image_model": "@cf/black-forest-labs/flux-2-klein-4b",
        "character_identity": "MIKO_CAT",
        "character_reference": "required",
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
        data = story_engine.generate_story(
            category=request.category,
            core_value=request.core_value,
            location=request.location,
            supporting_character=request.supporting_character,
            main_object=request.main_object,
            duration=request.duration,
            language=request.language,
            episode_id=request.episode_id,
        )
        return {"success": True, "data": data}
    except StoryEngineError as exc:
        return {"success": False, "error": str(exc)}


@app.post("/story/image-prompts")
async def generate_image_prompts(request: ImagePromptRequest):
    try:
        data = image_prompt_engine.generate_for_story(request.story)
        return {"success": True, **data}
    except ImagePromptEngineError as exc:
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        return {"success": False, "error": f"Unexpected image prompt error: {exc}"}


@app.post("/images/generate")
async def generate_image(http_request: Request, request: ImageGenerateRequest):
    try:
        env = http_request.scope.get("env")
        if env is None or getattr(env, "AI", None) is None:
            raise ImageGenerationEngineError("Workers AI binding is unavailable.")

        engine = ImageGenerationEngine(env.AI)
        data = await engine.generate(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            reference_image=request.reference_image,
            width=request.width,
            height=request.height,
            seed=request.seed,
            scene_number=request.scene_number,
        )
        return data
    except ImageGenerationEngineError as exc:
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        return {"success": False, "error": f"Image generation error: {exc}"}


@app.post("/videos/generate")
async def generate_video(http_request: Request, request: VideoGenerateRequest):
    try:
        env = http_request.scope.get("env")
        if env is None or getattr(env, "AI", None) is None:
            raise VideoGenerationConfigurationError(
                "Workers AI binding is unavailable."
            )

        engine = VideoGenerationEngine(env.AI)
        data = await engine.generate(
            image=request.image,
            motion_prompt=request.motion_prompt,
            duration=request.duration,
            resolution=request.resolution,
            fps=request.fps,
            draft=request.draft,
            seed=request.seed,
            scene_number=request.scene_number,
        )
        return data
    except (
        VideoGenerationError,
        VideoGenerationInputError,
        VideoGenerationConfigurationError,
    ) as exc:
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        return {"success": False, "error": f"Video generation error: {exc}"}


@app.get("/pipeline/status")
async def pipeline_status():
    return {
        "story_engine": "ready",
        "image_prompt_engine": "ready",
        "image_generation_engine": "ready",
        "video_generation_engine": "ready",
        "video_provider": "cloudflare-workers-ai",
        "video_model": "pruna/p-video",
        "image_provider": "cloudflare-workers-ai",
        "image_model": "@cf/black-forest-labs/flux-2-klein-4b",
        "character_identity": "MIKO_CAT",
        "character_reference": "required",
        "aspect_ratio": "9:16",
        "resolution": "576x1024",
    }


from workers import asgi

Default = asgi.entrypoint(app)
