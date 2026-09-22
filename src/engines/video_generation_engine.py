"""
Miko Video Generating Engine V1
Cloudflare Python Workers + fal.ai Queue API

Purpose:
- Generate a short vertical Miko video from an existing scene image.
- Uses fal.ai Kling Video 3 Standard Image-to-Video.
- Keeps the API key server-side.
- Uses the fal.ai async queue so the Worker does not wait for the whole render.

Important:
- `start_image_url` must be a publicly reachable image URL.
- Do not put FAL_KEY in frontend JavaScript.
- This engine does not upload browser data-URI images to storage yet.
  The frontend/storage layer should provide a hosted image URL first.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from js import fetch
from pyodide.ffi import to_js


class VideoGenerationError(Exception):
    """Base error for video generation."""


class FalAuthenticationError(VideoGenerationError):
    """Raised when FAL_KEY is missing or rejected."""


class FalRequestError(VideoGenerationError):
    """Raised when fal.ai rejects a request."""


class FalQueueError(VideoGenerationError):
    """Raised when a queue operation fails."""


class VideoGenerationEngine:
    """
    Server-side wrapper around fal.ai Kling Video 3 Standard I2V.

    Model:
        fal-ai/kling-video/v3/standard/image-to-video

    Flow:
        submit() -> request_id
        status() -> queue status
        result() -> generated video URL
    """

    MODEL = "fal-ai/kling-video/v3/standard/image-to-video"
    QUEUE_URL = f"https://queue.fal.run/{MODEL}"

    DEFAULT_DURATION = "5"
    DEFAULT_CFG_SCALE = 0.5

    DEFAULT_NEGATIVE_PROMPT = (
        "blur, distort, low quality, flicker, jitter, "
        "deformed face, deformed paws, extra limbs, extra legs, "
        "extra arms, duplicate character, changing fur color, "
        "changing clothes, human, human child, human body, "
        "wrong animal species, dog, fox, wolf, bear, rabbit, "
        "squirrel, scary scene, horror, violence"
    )

    MIKO_MOTION_LOCK = (
        "Keep Miko exactly consistent with the starting image. "
        "Miko is a cute 3D animated orange-and-white male kitten "
        "with a slightly oversized round feline head, small body, "
        "short feline legs, fluffy orange tail, cat ears, whiskers, "
        "dark-brown feline eyes, white muzzle and cheeks, white chest, "
        "white belly, white paws and white tail tip. "
        "Miko wears the same bright blue hoodie with white drawstrings "
        "and the same small paw pendant. "
        "Do not transform Miko into a human or another animal. "
        "Preserve the face, fur pattern, colors, clothing, body proportions "
        "and environment from the starting image."
    )

    def __init__(
        self,
        api_key: str,
        *,
        model: Optional[str] = None,
    ):
        self.api_key = (api_key or "").strip()
        self.model = model or self.MODEL
        self.queue_url = f"https://queue.fal.run/{self.model}"

        if not self.api_key:
            raise FalAuthenticationError(
                "FAL_KEY is not configured in the Cloudflare Worker."
            )

    @staticmethod
    def _duration(value: Any) -> str:
        allowed = {"3", "4", "5", "6", "7", "8", "9",
                   "10", "11", "12", "13", "14", "15"}
        value = str(value or "5")
        if value not in allowed:
            raise VideoGenerationError(
                f"Invalid duration '{value}'. "
                f"Allowed values: {', '.join(sorted(allowed, key=int))}"
            )
        return value

    @staticmethod
    def _require_url(value: str) -> str:
        value = (value or "").strip()
        if not value:
            raise VideoGenerationError("start_image_url is required.")

        if not (
            value.startswith("https://")
            or value.startswith("http://")
        ):
            raise VideoGenerationError(
                "start_image_url must be a public HTTP(S) URL. "
                "A browser data URI is not accepted by this V1 engine."
            )

        return value

    async def _fetch_json(
        self,
        url: str,
        *,
        method: str = "GET",
        payload: Optional[dict[str, Any]] = None,
    ) -> tuple[int, dict[str, Any], str]:
        headers = {
            "Authorization": f"Key {self.api_key}",
            "Accept": "application/json",
        }

        options: dict[str, Any] = {
            "method": method,
            "headers": headers,
        }

        if payload is not None:
            headers["Content-Type"] = "application/json"
            options["body"] = json.dumps(payload)

        response = await fetch(
            url,
            to_js(options, dict_converter="object"),
        )

        status_code = int(response.status)
        text = await response.text()

        try:
            data = json.loads(text) if text else {}
        except Exception:
            data = {"raw": text}

        return status_code, data, text

    def build_prompt(self, motion_prompt: str) -> str:
        motion = (motion_prompt or "").strip()

        if not motion:
            motion = (
                "Miko makes gentle natural movements, blinks naturally, "
                "looks around curiously, and moves his fluffy tail softly. "
                "The camera makes a subtle cinematic push-in."
            )

        return (
            f"{self.MIKO_MOTION_LOCK}\n\n"
            f"Scene motion:\n{motion}\n\n"
            "Animation direction: smooth children's animation, gentle natural "
            "movement, stable anatomy, stable character identity, coherent "
            "continuous motion, polished 3D animation, warm family-friendly "
            "cinematic lighting. Avoid sudden camera movement."
        )

    async def submit(
        self,
        *,
        start_image_url: str,
        motion_prompt: str,
        duration: str = DEFAULT_DURATION,
        negative_prompt: Optional[str] = None,
        generate_audio: bool = False,
        cfg_scale: float = DEFAULT_CFG_SCALE,
        scene_number: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Submit an image-to-video job.

        Returns the fal queue response, normally containing:
        request_id, status_url, response_url, cancel_url.
        """
        image_url = self._require_url(start_image_url)
        duration = self._duration(duration)

        prompt = self.build_prompt(motion_prompt)
        negative = (
            negative_prompt.strip()
            if isinstance(negative_prompt, str) and negative_prompt.strip()
            else self.DEFAULT_NEGATIVE_PROMPT
        )

        payload = {
            "prompt": prompt,
            "start_image_url": image_url,
            "duration": duration,
            "generate_audio": bool(generate_audio),
            "negative_prompt": negative,
            "cfg_scale": float(cfg_scale),
        }

        status_code, data, raw = await self._fetch_json(
            self.queue_url,
            method="POST",
            payload=payload,
        )

        if status_code in (401, 403):
            raise FalAuthenticationError(
                f"fal.ai authentication failed ({status_code})."
            )

        if status_code < 200 or status_code >= 300:
            message = (
                data.get("detail")
                or data.get("message")
                or data.get("error")
                or raw
            )
            raise FalRequestError(
                f"fal.ai submit failed ({status_code}): {message}"
            )

        request_id = data.get("request_id")
        if not request_id:
            raise FalQueueError(
                f"fal.ai did not return request_id: {data}"
            )

        return {
            "success": True,
            "provider": "fal.ai",
            "model": self.model,
            "scene_number": scene_number,
            "request_id": request_id,
            "status_url": data.get("status_url"),
            "response_url": data.get("response_url"),
            "cancel_url": data.get("cancel_url"),
            "duration": duration,
            "generate_audio": bool(generate_audio),
            "character_lock": "MIKO_STRICT",
            "status": "IN_QUEUE",
        }

    async def status(
        self,
        request_id: str,
        *,
        status_url: Optional[str] = None,
        logs: bool = False,
    ) -> dict[str, Any]:
        """Get the current fal queue status."""
        request_id = (request_id or "").strip()
        if not request_id:
            raise FalQueueError("request_id is required.")

        url = status_url or (
            f"{self.queue_url}/requests/{request_id}/status"
        )

        if logs:
            url += "?logs=1"

        status_code, data, raw = await self._fetch_json(url)

        if status_code == 404:
            raise FalQueueError(
                f"fal.ai request not found: {request_id}"
            )

        if status_code < 200 or status_code >= 300:
            message = (
                data.get("detail")
                or data.get("message")
                or data.get("error")
                or raw
            )
            raise FalQueueError(
                f"fal.ai status failed ({status_code}): {message}"
            )

        return {
            "success": True,
            "provider": "fal.ai",
            "model": self.model,
            "request_id": request_id,
            "status": data.get("status"),
            "queue_position": data.get("queue_position"),
            "logs": data.get("logs"),
            "raw": data,
        }

    async def result(
        self,
        request_id: str,
        *,
        response_url: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Fetch the completed result.

        Expected successful result shape:
        {
            "video": {
                "url": "...",
                "content_type": "video/mp4",
                ...
            }
        }
        """
        request_id = (request_id or "").strip()
        if not request_id:
            raise FalQueueError("request_id is required.")

        url = response_url or (
            f"{self.queue_url}/requests/{request_id}"
        )

        status_code, data, raw = await self._fetch_json(url)

        if status_code < 200 or status_code >= 300:
            message = (
                data.get("detail")
                or data.get("message")
                or data.get("error")
                or raw
            )
            raise FalQueueError(
                f"fal.ai result failed ({status_code}): {message}"
            )

        video = data.get("video")
        if not isinstance(video, dict):
            raise FalQueueError(
                f"fal.ai result has no video object: {data}"
            )

        video_url = video.get("url")
        if not video_url:
            raise FalQueueError(
                f"fal.ai video result has no URL: {video}"
            )

        return {
            "success": True,
            "provider": "fal.ai",
            "model": self.model,
            "request_id": request_id,
            "status": "COMPLETED",
            "video": video,
            "video_url": video_url,
        }

    async def cancel(
        self,
        request_id: str,
        *,
        cancel_url: Optional[str] = None,
    ) -> dict[str, Any]:
        """Cancel a queued/running job when supported by fal."""
        request_id = (request_id or "").strip()
        if not request_id:
            raise FalQueueError("request_id is required.")

        url = cancel_url or (
            f"{self.queue_url}/requests/{request_id}/cancel"
        )

        status_code, data, raw = await self._fetch_json(
            url,
            method="PUT",
        )

        if status_code < 200 or status_code >= 300:
            message = (
                data.get("detail")
                or data.get("message")
                or data.get("error")
                or raw
            )
            raise FalQueueError(
                f"fal.ai cancel failed ({status_code}): {message}"
            )

        return {
            "success": True,
            "provider": "fal.ai",
            "model": self.model,
            "request_id": request_id,
            "status": "CANCELLED",
            "raw": data,
        }


__all__ = [
    "VideoGenerationEngine",
    "VideoGenerationError",
    "FalAuthenticationError",
    "FalRequestError",
    "FalQueueError",
]
