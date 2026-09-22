from __future__ import annotations

from typing import Any


class ImageGenerationError(Exception):
    """Base error for image generation."""


class ImageGenerationEngine:
    """
    Cloudflare Workers AI image generation engine.

    Provider:
        @cf/black-forest-labs/flux-1-schnell

    The engine receives the already-built visual prompt from the
    Image Prompt Engine and sends it to Workers AI. The generated
    image is returned as a data URI so the frontend can preview it
    immediately without requiring storage yet.
    """

    MODEL = "@cf/black-forest-labs/flux-1-schnell"
    VERSION = "1.0.0"
    DEFAULT_STEPS = 4
    MAX_STEPS = 8
    MAX_PROMPT_LENGTH = 2048

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

    async def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        steps: int = DEFAULT_STEPS,
        seed: int | None = None,
    ) -> dict[str, Any]:
        try:
            from workers import env
        except Exception as exc:
            raise ImageGenerationError(
                f"Workers AI binding is unavailable: {exc}"
            ) from exc

        clean_prompt = self._clean_prompt(prompt)
        clean_negative = self._clean_negative_prompt(negative_prompt)

        try:
            steps_value = int(steps)
        except (TypeError, ValueError):
            steps_value = self.DEFAULT_STEPS

        steps_value = max(1, min(self.MAX_STEPS, steps_value))

        # FLUX.1 schnell's documented binding input is prompt + optional
        # seed/steps. We include the negative prompt in the prompt itself
        # because this model's documented schema does not expose a
        # dedicated negative_prompt parameter.
        final_prompt = clean_prompt
        if clean_negative:
            final_prompt += (
                "\n\nAVOID / NEGATIVE CONSTRAINTS:\n"
                + clean_negative
            )

        payload: dict[str, Any] = {
            "prompt": final_prompt,
            "steps": steps_value,
        }

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
                    "Please check the Workers AI usage/quota and try again later."
                ) from exc
            raise ImageGenerationError(
                f"Workers AI image generation failed: {message}"
            ) from exc

        image_base64 = None

        try:
            image_base64 = result.image
        except Exception:
            pass

        if not image_base64:
            try:
                image_base64 = result["image"]
            except Exception:
                pass

        if not image_base64:
            raise ImageGenerationError(
                "Workers AI returned no image data."
            )

        image_base64 = str(image_base64)

        # Cloudflare's FLUX.1 schnell example returns JPEG base64.
        data_uri = f"data:image/jpeg;base64,{image_base64}"

        return {
            "success": True,
            "provider": self.provider,
            "model": self.model,
            "engine_version": self.VERSION,
            "data_uri": data_uri,
            "image_base64": image_base64,
            "mime_type": "image/jpeg",
            "aspect_ratio": "9:16",
            "resolution": "1080x1920 target",
            "steps": steps_value,
            "seed": payload.get("seed"),
        }


image_generation_engine = ImageGenerationEngine()
