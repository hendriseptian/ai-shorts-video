"""
Miko Video Generating Engine V2
Cloudflare Workers AI / P-Video

This version intentionally removes the R2 and fal.ai dependency.

The generated Miko image is passed directly as a Base64 data URI to
Cloudflare Workers AI. The P-Video model supports image-to-video and
accepts an image as a URL or data URI.

Model:
    pruna/p-video

This keeps the architecture:

Browser
  -> Cloudflare Worker
  -> Workers AI
  -> video URL

No R2 bucket and no fal.ai API key are required by this engine.

IMPORTANT:
Workers AI has a daily free allocation. Actual model usage consumes
Neurons. The free allocation is not a guarantee that an unlimited number
of videos can be generated for free.
"""

from __future__ import annotations

from typing import Any, Optional


class VideoGenerationError(Exception):
    """Base video generation error."""


class VideoGenerationConfigurationError(VideoGenerationError):
    """Workers AI binding is unavailable."""


class VideoGenerationInputError(VideoGenerationError):
    """Invalid video input."""


class VideoGenerationEngine:
    """
    Cloudflare Workers AI image-to-video engine.

    Expected Worker binding:
        AI

    Model:
        pruna/p-video
    """

    MODEL = "pruna/p-video"

    DEFAULT_DURATION = 5
    DEFAULT_RESOLUTION = "720p"
    DEFAULT_FPS = 24
    DEFAULT_DRAFT = True

    DEFAULT_NEGATIVE_PROMPT = (
        "flicker, jitter, unstable anatomy, deformed face, deformed paws, "
        "extra limbs, duplicate character, changing fur color, changing "
        "clothes, human, human child, human body, wrong animal species, "
        "dog, fox, wolf, bear, rabbit, squirrel, horror, violence"
    )

    MIKO_MOTION_LOCK = (
        "Keep Miko exactly consistent with the starting image. "
        "Miko is a cute 3D animated orange-and-white male kitten with a "
        "slightly oversized round feline head, small body, short feline "
        "legs, fluffy orange tail, cat ears, whiskers, dark-brown feline "
        "eyes, white muzzle and cheeks, white chest, white belly, white "
        "paws and white tail tip. Miko wears the same bright blue hoodie "
        "with white drawstrings and the same small paw pendant. "
        "Do not transform Miko into a human or another animal. Preserve "
        "the face, fur pattern, colors, clothing, body proportions and "
        "environment from the starting image."
    )

    def __init__(self, ai: Any):
        if ai is None:
            raise VideoGenerationConfigurationError(
                "Workers AI binding 'AI' is not available."
            )
        self.ai = ai

    @classmethod
    def from_env(cls, env: Any) -> "VideoGenerationEngine":
        ai = getattr(env, "AI", None)
        return cls(ai)

    @staticmethod
    def _validate_image(image: str) -> str:
        if not isinstance(image, str) or not image.strip():
            raise VideoGenerationInputError(
                "image is required."
            )

        value = image.strip()

        allowed = (
            value.startswith("data:image/png;base64,")
            or value.startswith("data:image/jpeg;base64,")
            or value.startswith("data:image/jpg;base64,")
            or value.startswith("data:image/webp;base64,")
        )

        if not allowed:
            raise VideoGenerationInputError(
                "image must be a PNG, JPEG or WebP Base64 data URI."
            )

        return value

    @staticmethod
    def _validate_duration(duration: Any) -> int:
        try:
            value = int(duration)
        except (TypeError, ValueError) as exc:
            raise VideoGenerationInputError(
                "duration must be an integer."
            ) from exc

        if value < 1 or value > 20:
            raise VideoGenerationInputError(
                "duration must be between 1 and 20 seconds."
            )

        return value

    @staticmethod
    def _validate_resolution(resolution: str) -> str:
        value = str(resolution or "720p").strip().lower()

        if value not in {"720p", "1080p"}:
            raise VideoGenerationInputError(
                "resolution must be 720p or 1080p."
            )

        return value

    @staticmethod
    def _validate_fps(fps: Any) -> int:
        try:
            value = int(fps)
        except (TypeError, ValueError) as exc:
            raise VideoGenerationInputError(
                "fps must be an integer."
            ) from exc

        if value not in {24, 25, 30, 48}:
            raise VideoGenerationInputError(
                "fps must be one of 24, 25, 30 or 48."
            )

        return value

    def build_prompt(self, motion_prompt: str) -> str:
        motion = (motion_prompt or "").strip()

        if not motion:
            motion = (
                "Miko makes gentle natural movements, blinks naturally, "
                "looks around curiously, and moves his fluffy tail softly. "
                "The camera makes a subtle slow push-in."
            )

        return (
            f"{self.MIKO_MOTION_LOCK}\n\n"
            f"Scene motion:\n{motion}\n\n"
            "Animation direction: smooth children's animation, gentle "
            "natural movement, stable anatomy, stable character identity, "
            "coherent continuous motion, polished 3D animation, warm "
            "family-friendly cinematic lighting. Avoid sudden motion."
        )

    async def generate(
        self,
        *,
        image: str,
        motion_prompt: str,
        duration: int = DEFAULT_DURATION,
        resolution: str = DEFAULT_RESOLUTION,
        fps: int = DEFAULT_FPS,
        draft: bool = DEFAULT_DRAFT,
        seed: Optional[int] = None,
        scene_number: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Generate a video directly through Workers AI.

        `image` is the generated Miko scene image data URI already held
        by the browser/frontend.
        """
        image = self._validate_image(image)
        duration = self._validate_duration(duration)
        resolution = self._validate_resolution(resolution)
        fps = self._validate_fps(fps)

        prompt = self.build_prompt(motion_prompt)

        payload: dict[str, Any] = {
            "prompt": prompt,
            "image": image,
            "duration": duration,
            "resolution": resolution,
            "fps": fps,
            "draft": bool(draft),
            "save_audio": False,
            "prompt_upsampling": True,
        }

        if seed is not None:
            payload["seed"] = int(seed)

        try:
            response = await self.ai.run(self.MODEL, payload)
        except Exception as exc:
            message = str(exc)
            if "quota" in message.lower() or "allocation" in message.lower():
                raise VideoGenerationError(
                    "Workers AI free allocation/quota was reached. "
                    "Try again after the daily reset or reduce usage."
                ) from exc

            raise VideoGenerationError(
                f"Workers AI video generation failed: {message}"
            ) from exc

        video_url = None

        if isinstance(response, dict):
            video_url = response.get("video")

            if not video_url:
                result = response.get("result")
                if isinstance(result, dict):
                    video_url = result.get("video")

        if not video_url:
            raise VideoGenerationError(
                f"Workers AI returned no video URL. Response: {response}"
            )

        return {
            "success": True,
            "provider": "cloudflare-workers-ai",
            "model": self.MODEL,
            "scene_number": scene_number,
            "video_url": video_url,
            "duration": duration,
            "resolution": resolution,
            "fps": fps,
            "draft": bool(draft),
            "audio": False,
            "character_lock": "MIKO_STRICT",
            "status": "COMPLETED",
        }


__all__ = [
    "VideoGenerationEngine",
    "VideoGenerationError",
    "VideoGenerationConfigurationError",
    "VideoGenerationInputError",
]
