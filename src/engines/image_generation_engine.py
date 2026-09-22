from __future__ import annotations

import base64
from typing import Any


class ImageGenerationError(Exception):
    """Base error for image generation."""


class ImageGenerationEngine:
    """
    Cloudflare Workers AI image generation engine for vertical Shorts.

    Provider:
        @cf/bytedance/stable-diffusion-xl-lightning

    This model supports explicit width/height, so the backend requests an
    actual 9:16 canvas instead of merely labeling a square image as 9:16.
    """

    MODEL = "@cf/bytedance/stable-diffusion-xl-lightning"
    VERSION = "2.0.1"
    DEFAULT_STEPS = 4
    MAX_STEPS = 20
    MAX_PROMPT_LENGTH = 2048

    # Development/final-friendly vertical canvas. Exact 9:16 ratio.
    DEFAULT_WIDTH = 576
    DEFAULT_HEIGHT = 1024

    def __init__(self) -> None:
        self.provider = "cloudflare-workers-ai"
        self.model = self.MODEL

    def status(self) -> dict[str, Any]:
        return {
            "ready": True,
            "provider": self.provider,
            "model": self.model,
            "version": self.VERSION,
            "output": "base64-data-uri",
            "aspect_ratio_target": "9:16",
            "width": self.DEFAULT_WIDTH,
            "height": self.DEFAULT_HEIGHT,
        }

    @staticmethod
    def _clean_prompt(prompt: str) -> str:
        value = str(prompt or "").strip()
        if not value:
            raise ImageGenerationError("Image prompt is required.")
        if len(value) > ImageGenerationEngine.MAX_PROMPT_LENGTH:
            value = value[: ImageGenerationEngine.MAX_PROMPT_LENGTH]
        return value

    @staticmethod
    def _clean_negative_prompt(prompt: str) -> str:
        value = str(prompt or "").strip()
        if len(value) > ImageGenerationEngine.MAX_PROMPT_LENGTH:
            value = value[: ImageGenerationEngine.MAX_PROMPT_LENGTH]
        return value

    @staticmethod
    def _parse_resolution(resolution: str) -> tuple[int, int]:
        """Return a safe exact-9:16 resolution; fall back to 576x1024."""
        try:
            raw = str(resolution or "").lower().replace(" ", "")
            if "x" in raw:
                w_text, h_text = raw.split("x", 1)
                width = int(w_text)
                height = int(h_text)
            else:
                raise ValueError
        except Exception:
            return ImageGenerationEngine.DEFAULT_WIDTH, ImageGenerationEngine.DEFAULT_HEIGHT

        # We intentionally constrain output to a stable 9:16 canvas.
        # Keep the requested size only if it is an exact 9:16 ratio and
        # within the model's documented 256..2048 range.
        if width < 256 or height < 256 or width > 2048 or height > 2048:
            return ImageGenerationEngine.DEFAULT_WIDTH, ImageGenerationEngine.DEFAULT_HEIGHT

        if width * 16 != height * 9:
            return ImageGenerationEngine.DEFAULT_WIDTH, ImageGenerationEngine.DEFAULT_HEIGHT

        # Model dimensions are safest when divisible by 8.
        width = (width // 8) * 8
        height = (height // 8) * 8

        if width * 16 != height * 9 or width < 256 or height < 256:
            return ImageGenerationEngine.DEFAULT_WIDTH, ImageGenerationEngine.DEFAULT_HEIGHT

        return width, height

    @staticmethod
    def _get_value(result: Any, key: str) -> Any:
        try:
            value = getattr(result, key)
            if value is not None:
                return value
        except Exception:
            pass
        try:
            if isinstance(result, dict):
                return result.get(key)
        except Exception:
            pass
        try:
            value = result[key]
            if value is not None:
                return value
        except Exception:
            pass
        return None

    async def _extract_base64(self, result: Any) -> str | None:
        """Extract image bytes from the Workers AI ReadableStream.

        SDXL-Lightning returns a ReadableStream. In Python Workers, the most
        reliable way to consume that stream is to wrap it in the Fetch API
        Response, read its ArrayBuffer, then convert the ArrayBuffer to bytes.
        """

        # Some models/runtimes may return an object containing base64 directly.
        for key in ("image", "image_b64", "image_base64"):
            value = self._get_value(result, key)
            if value:
                if isinstance(value, str):
                    return value
                if isinstance(value, (bytes, bytearray, memoryview)):
                    return base64.b64encode(bytes(value)).decode("ascii")

        # SDXL-Lightning currently returns a ReadableStream. Use the native
        # Workers Fetch Response API to consume the stream completely.
        try:
            from js import Response as JSResponse

            response = JSResponse.new(result)
            array_buffer = await response.arrayBuffer()
            raw_bytes = array_buffer.to_bytes()

            if raw_bytes:
                return base64.b64encode(raw_bytes).decode("ascii")
        except Exception as exc:
            raise ImageGenerationError(
                f"Could not read generated image stream: {exc}"
            ) from exc

        return None

    async def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        steps: int = DEFAULT_STEPS,
        seed: int | None = None,
        resolution: str = "576x1024",
    ) -> dict[str, Any]:
        try:
            from workers import env
        except Exception as exc:
            raise ImageGenerationError(
                f"Workers AI binding is unavailable: {exc}"
            ) from exc

        clean_prompt = self._clean_prompt(prompt)
        clean_negative = self._clean_negative_prompt(negative_prompt)
        width, height = self._parse_resolution(resolution)

        try:
            steps_value = int(steps)
        except (TypeError, ValueError):
            steps_value = self.DEFAULT_STEPS
        steps_value = max(1, min(self.MAX_STEPS, steps_value))

        payload: dict[str, Any] = {
            "prompt": clean_prompt,
            "width": width,
            "height": height,
            "num_steps": steps_value,
        }

        if clean_negative:
            payload["negative_prompt"] = clean_negative

        if seed is not None:
            try:
                payload["seed"] = int(seed)
            except (TypeError, ValueError):
                pass

        try:
            result = await env.AI.run(self.MODEL, payload)
        except Exception as exc:
            message = str(exc)
            if "quota" in message.lower() or "neuron" in message.lower():
                raise ImageGenerationError(
                    "Workers AI image generation quota was reached. "
                    "Please check Workers AI usage/quota and try again later."
                ) from exc
            raise ImageGenerationError(
                f"Workers AI image generation failed: {message}"
            ) from exc

        image_base64 = await self._extract_base64(result)
        if not image_base64:
            raise ImageGenerationError(
                "Workers AI returned no image data. "
                "The model response format may have changed."
            )

        return {
            "success": True,
            "provider": self.provider,
            "model": self.model,
            "engine_version": self.VERSION,
            "data_uri": f"data:image/jpeg;base64,{image_base64}",
            "image_base64": image_base64,
            "mime_type": "image/jpeg",
            "aspect_ratio": "9:16",
            "resolution": f"{width}x{height}",
            "width": width,
            "height": height,
            "steps": steps_value,
            "seed": payload.get("seed"),
        }


image_generation_engine = ImageGenerationEngine()
