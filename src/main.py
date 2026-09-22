from __future__ import annotations

import json
from urllib.parse import urlparse

from workers import WorkerEntrypoint, Response

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
APP_VERSION = "0.6.0"

story_engine = StoryEngine()
image_prompt_engine = ImagePromptEngine()


class Default(WorkerEntrypoint):
    """Native Cloudflare Python Worker without FastAPI/Pydantic/ASGI."""

    def _headers(self):
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Content-Type": "application/json; charset=utf-8",
        }

    def _json(self, data, status=200):
        return Response(
            json.dumps(data, ensure_ascii=False),
            status=status,
            headers=self._headers(),
        )

    async def _read_json(self, request):
        try:
            body = await request.json()
        except Exception as exc:
            raise ValueError(f"Invalid JSON body: {exc}") from exc

        if not isinstance(body, dict):
            raise ValueError("Request body must be a JSON object.")

        return body

    @staticmethod
    def _optional_string(body, key):
        value = body.get(key)
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string.")
        value = value.strip()
        return value or None

    @staticmethod
    def _required_string(body, key):
        value = body.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} is required.")
        return value.strip()

    @staticmethod
    def _int_value(body, key, default, minimum=None, maximum=None):
        value = body.get(key, default)
        try:
            value = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} must be an integer.") from exc

        if minimum is not None and value < minimum:
            raise ValueError(f"{key} must be >= {minimum}.")
        if maximum is not None and value > maximum:
            raise ValueError(f"{key} must be <= {maximum}.")
        return value

    @staticmethod
    def _optional_int(body, key):
        value = body.get(key)
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{key} must be an integer.") from exc

    async def _story_generate(self, request):
        body = await self._read_json(request)

        language = body.get("language", "id")
        if not isinstance(language, str) or not 2 <= len(language) <= 5:
            raise ValueError("language must be a string with 2-5 characters.")

        try:
            data = story_engine.generate_story(
                category=self._optional_string(body, "category"),
                core_value=self._optional_string(body, "core_value"),
                location=self._optional_string(body, "location"),
                supporting_character=self._optional_string(
                    body, "supporting_character"
                ),
                main_object=self._optional_string(body, "main_object"),
                duration=self._int_value(
                    body, "duration", 60, minimum=10, maximum=180
                ),
                language=language,
                episode_id=self._optional_string(body, "episode_id"),
            )
            return self._json({"success": True, "data": data})
        except StoryEngineError as exc:
            return self._json({"success": False, "error": str(exc)}, 400)

    async def _image_prompts(self, request):
        body = await self._read_json(request)
        story = body.get("story")

        if not isinstance(story, dict):
            raise ValueError("story must be a JSON object.")

        try:
            data = image_prompt_engine.generate_for_story(story)
            return self._json({"success": True, **data})
        except ImagePromptEngineError as exc:
            return self._json({"success": False, "error": str(exc)}, 400)
        except Exception as exc:
            return self._json(
                {
                    "success": False,
                    "error": f"Unexpected image prompt error: {exc}",
                },
                500,
            )

    async def _image_generate(self, request):
        body = await self._read_json(request)

        ai = getattr(self.env, "AI", None)
        if ai is None:
            raise ImageGenerationEngineError(
                "Workers AI binding is unavailable."
            )

        engine = ImageGenerationEngine(ai)

        data = await engine.generate(
            prompt=self._required_string(body, "prompt"),
            negative_prompt=body.get("negative_prompt", ""),
            reference_image=self._required_string(body, "reference_image"),
            width=self._int_value(
                body, "width", 576, minimum=256, maximum=1920
            ),
            height=self._int_value(
                body, "height", 1024, minimum=256, maximum=1920
            ),
            seed=self._optional_int(body, "seed"),
            scene_number=self._optional_int(body, "scene_number"),
        )

        return self._json(data)

    async def _video_generate(self, request):
        body = await self._read_json(request)

        ai = getattr(self.env, "AI", None)
        if ai is None:
            raise VideoGenerationConfigurationError(
                "Workers AI binding is unavailable."
            )

        resolution = body.get("resolution", "720p")
        if not isinstance(resolution, str):
            raise ValueError("resolution must be a string.")

        fps = self._int_value(body, "fps", 24, minimum=1, maximum=60)

        draft = body.get("draft", True)
        if not isinstance(draft, bool):
            draft = bool(draft)

        engine = VideoGenerationEngine(ai)

        data = await engine.generate(
            image=self._required_string(body, "image"),
            motion_prompt=body.get("motion_prompt", ""),
            duration=self._int_value(
                body, "duration", 5, minimum=1, maximum=20
            ),
            resolution=resolution,
            fps=fps,
            draft=draft,
            seed=self._optional_int(body, "seed"),
            scene_number=self._optional_int(body, "scene_number"),
        )

        return self._json(data)

    async def fetch(self, request):
        try:
            if request.method == "OPTIONS":
                return Response("", status=204, headers=self._headers())

            parsed = urlparse(str(request.url))
            path = parsed.path.rstrip("/") or "/"
            method = request.method.upper()

            if method == "GET" and path == "/":
                return self._json({
                    "name": APP_NAME,
                    "version": APP_VERSION,
                    "platform": "cloudflare-python-workers",
                    "architecture": "native-worker",
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
                })

            if method == "GET" and path == "/health":
                return self._json({
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
                    "architecture": "native-worker",
                })

            if method == "GET" and path == "/bibles":
                return self._json(story_engine.get_bibles())

            if method == "GET" and path == "/story/options":
                return self._json(story_engine.get_options())

            if method == "GET" and path == "/pipeline/status":
                return self._json({
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
                    "architecture": "native-worker",
                })

            if method == "POST" and path == "/story/generate":
                return await self._story_generate(request)

            if method == "POST" and path == "/story/image-prompts":
                return await self._image_prompts(request)

            if method == "POST" and path == "/images/generate":
                try:
                    return await self._image_generate(request)
                except ImageGenerationEngineError as exc:
                    return self._json(
                        {"success": False, "error": str(exc)}, 500
                    )

            if method == "POST" and path == "/videos/generate":
                try:
                    return await self._video_generate(request)
                except (
                    VideoGenerationError,
                    VideoGenerationInputError,
                    VideoGenerationConfigurationError,
                ) as exc:
                    return self._json(
                        {"success": False, "error": str(exc)}, 500
                    )

            return self._json(
                {"success": False, "error": f"Route not found: {path}"},
                404,
            )

        except ValueError as exc:
            return self._json({"success": False, "error": str(exc)}, 400)
        except Exception as exc:
            return self._json(
                {"success": False, "error": f"Worker error: {exc}"},
                500,
            )


__all__ = ["Default"]
