"""
Miko Video Generation Engine V3
Designed to plug directly into the user's current main.py.

Expected main.py call:

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

No R2.
No fal.ai.
No ContextVar.
No FastAPI imports.
No Worker request/environment access.

Workers AI binding is passed directly as `env.AI`.
"""

from __future__ import annotations

from typing import Any, Optional


class VideoGenerationError(Exception):
    """Base video generation error."""


class VideoGenerationInputError(VideoGenerationError):
    """Invalid video generation input."""


class VideoGenerationConfigurationError(VideoGenerationError):
    """Workers AI configuration error."""


class VideoGenerationEngine:
    MODEL = "pruna/p-video"

    DEFAULT_DURATION = 5
    DEFAULT_RESOLUTION = "720p"
    DEFAULT_FPS = 24
    DEFAULT_DRAFT = True

    DEFAULT_NEGATIVE_PROMPT = (
        "flicker, jitter, unstable anatomy, deformed face, deformed paws, "
        "extra limbs, extra legs, extra arms, duplicate character, "
        "changing fur color, changing clothes, human, human child, "
        "human body, humanoid, wrong animal species, dog, puppy, fox, "
        "wolf, bear, rabbit, squirrel, scary scene, horror, violence, "
        "blood, injury, weapon, frightening imagery"
    )

    MIKO_CHARACTER_LOCK = (
        "Miko must remain exactly the same character as the starting image. "
        "Miko is a cute 3D animated male kitten/cat, orange-and-white fur, "
        "slightly oversized round feline head, small kitten body, short "
        "feline legs, triangular cat ears, dark-brown feline eyes, feline "
        "nose, whiskers, white muzzle and cheeks, white chest, white belly, "
        "white paws, white tail tip, fluffy orange feline tail. "
        "Miko wears a bright blue hoodie with white drawstrings and a small "
        "round paw pendant. Keep the same face, fur pattern, clothing, "
        "body proportions and colors throughout the entire video. "
        "Never turn Miko into a human or another animal."
    )

    def __init__(self, ai: Any):
        if ai is None:
            raise VideoGenerationConfigurationError(
                "Workers AI binding 'AI' is unavailable."
            )

        self.ai = ai

    @staticmethod
    def _validate_image(image: Any) -> str:
        if not isinstance(image, str) or not image.strip():
            raise VideoGenerationInputError(
                "image is required."
            )

        value = image.strip()

        accepted_prefixes = (
            "data:image/png;base64,",
            "data:image/jpeg;base64,",
            "data:image/jpg;base64,",
            "data:image/webp;base64,",
        )

        if not value.startswith(accepted_prefixes):
            raise VideoGenerationInputError(
                "image must be a PNG, JPEG or WebP Base64 data URI."
            )

        return value

    @staticmethod
    def _validate_duration(value: Any) -> int:
        try:
            duration = int(value)
        except (TypeError, ValueError) as exc:
            raise VideoGenerationInputError(
                "duration must be an integer."
            ) from exc

        # P-Video is tested here with the 5-second workflow.
        # Keep the public endpoint constrained to safe short-form values.
        if duration not in {5, 10}:
            raise VideoGenerationInputError(
                "For Miko V1, duration must be 5 or 10 seconds."
            )

        return duration

    @staticmethod
    def _validate_resolution(value: Any) -> str:
        resolution = str(value or "720p").strip().lower()

        if resolution not in {"720p", "1080p"}:
            raise VideoGenerationInputError(
                "resolution must be 720p or 1080p."
            )

        return resolution

    @staticmethod
    def _validate_fps(value: Any) -> int:
        try:
            fps = int(value)
        except (TypeError, ValueError) as exc:
            raise VideoGenerationInputError(
                "fps must be an integer."
            ) from exc

        if fps not in {24, 25, 30}:
            raise VideoGenerationInputError(
                "fps must be 24, 25 or 30."
            )

        return fps

    @staticmethod
    def _validate_seed(value: Any) -> Optional[int]:
        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise VideoGenerationInputError(
                "seed must be an integer."
            ) from exc

    def build_prompt(self, motion_prompt: str) -> str:
        motion = (motion_prompt or "").strip()

        if not motion:
            motion = (
                "Miko gently looks around with curiosity, blinks naturally, "
                "moves one paw softly, and gently moves his fluffy tail. "
                "The camera performs a subtle slow push-in."
            )

        return (
            f"{self.MIKO_CHARACTER_LOCK}\n\n"
            "Animate the existing starting image. Do not redesign the "
            "character or scene.\n\n"
            f"Motion direction:\n{motion}\n\n"
            "Use smooth, gentle, child-friendly 3D animation. "
            "Preserve stable anatomy and stable character identity. "
            "Use natural facial movement and subtle body motion. "
            "Avoid sudden camera movement, scene changes, morphing, "
            "character duplication, or object deformation."
        )

    def _build_payload(
        self,
        *,
        image: str,
        motion_prompt: str,
        duration: int,
        resolution: str,
        fps: int,
        draft: bool,
        seed: Optional[int],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "prompt": self.build_prompt(motion_prompt),
            "image": image,
            "duration": duration,
            "resolution": resolution,
            "fps": fps,
            "draft": bool(draft),
            "save_audio": False,
            "negative_prompt": self.DEFAULT_NEGATIVE_PROMPT,
        }

        if seed is not None:
            payload["seed"] = seed

        return payload

    @staticmethod
    def _extract_video_url(response: Any) -> Optional[str]:
        """
        Handle the common Workers AI response shapes without assuming
        that every runtime serializes the result identically.
        """
        if isinstance(response, str):
            if response.startswith(("http://", "https://")):
                return response
            return None

        if isinstance(response, dict):
            for key in ("video", "video_url", "url"):
                value = response.get(key)

                if isinstance(value, str) and value:
                    return value

                if isinstance(value, dict):
                    nested = value.get("url")
                    if isinstance(nested, str) and nested:
                        return nested

            result = response.get("result")
            if isinstance(result, dict):
                return VideoGenerationEngine._extract_video_url(result)

        return None

    @staticmethod
    def _response_debug(response: Any) -> str:
        try:
            return repr(response)[:2000]
        except Exception:
            return "<unserializable Workers AI response>"

    async def generate(
        self,
        *,
        image: str,
        motion_prompt: str = "",
        duration: int = DEFAULT_DURATION,
        resolution: str = DEFAULT_RESOLUTION,
        fps: int = DEFAULT_FPS,
        draft: bool = DEFAULT_DRAFT,
        seed: Optional[int] = None,
        scene_number: Optional[int] = None,
    ) -> dict[str, Any]:
        image = self._validate_image(image)
        duration = self._validate_duration(duration)
        resolution = self._validate_resolution(resolution)
        fps = self._validate_fps(fps)
        seed = self._validate_seed(seed)

        payload = self._build_payload(
            image=image,
            motion_prompt=motion_prompt,
            duration=duration,
            resolution=resolution,
            fps=fps,
            draft=draft,
            seed=seed,
        )

        try:
            response = await self.ai.run(
                self.MODEL,
                payload,
            )
        except Exception as exc:
            message = str(exc)

            lowered = message.lower()

            if (
                "quota" in lowered
                or "allocation" in lowered
                or "neurons" in lowered
            ):
                raise VideoGenerationError(
                    "Workers AI quota/free allocation was reached. "
                    f"Original error: {message}"
                ) from exc

            raise VideoGenerationError(
                f"Workers AI P-Video generation failed: {message}"
            ) from exc

        video_url = self._extract_video_url(response)

        if not video_url:
            raise VideoGenerationError(
                "P-Video returned no video URL. "
                f"Raw response: {self._response_debug(response)}"
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
            "character_identity": "MIKO_CAT",
            "character_lock": "STRICT",
            "status": "COMPLETED",
        }


__all__ = [
    "VideoGenerationEngine",
    "VideoGenerationError",
    "VideoGenerationInputError",
    "VideoGenerationConfigurationError",
]
