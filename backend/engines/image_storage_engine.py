"""
Miko Image Storage Engine V1
Cloudflare Python Workers + R2

Purpose:
- Accept a generated Miko image as a data URI or raw bytes.
- Store it in a Cloudflare R2 bucket through an R2 binding.
- Return a stable public URL when a public R2 base URL is configured.

The engine is intentionally independent from FastAPI so it can be
called from the existing Worker endpoints.
"""

from __future__ import annotations

import base64
import binascii
import re
import time
import uuid
from typing import Any, Optional


class ImageStorageError(Exception):
    """Base storage error."""


class ImageDataError(ImageStorageError):
    """Raised for invalid image data."""


class ImageStorageConfigurationError(ImageStorageError):
    """Raised when R2 configuration is missing."""


class ImageStorageEngine:
    """
    Cloudflare R2 image storage wrapper.

    Expected Worker binding:
        MIKO_MEDIA

    Expected optional Worker environment variable:
        MIKO_MEDIA_PUBLIC_URL

    Example:
        https://pub-xxxxxxxx.r2.dev
        or
        https://media.example.com

    The public URL is only a URL constructor. R2 itself must be configured
    for public access through r2.dev or a custom domain.
    """

    DEFAULT_BINDING = "MIKO_MEDIA"
    DEFAULT_PREFIX = "miko/images"

    DATA_URI_RE = re.compile(
        r"^data:(?P<mime>[\w.+-]+/[\w.+-]+)"
        r"(?:;charset=[^;,]+)?;base64,(?P<data>[A-Za-z0-9+/=\s]+)$",
        re.IGNORECASE,
    )

    def __init__(
        self,
        bucket: Any,
        *,
        public_base_url: Optional[str] = None,
        prefix: str = DEFAULT_PREFIX,
    ):
        if bucket is None:
            raise ImageStorageConfigurationError(
                "R2 binding MIKO_MEDIA is not available."
            )

        self.bucket = bucket
        self.public_base_url = (public_base_url or "").strip().rstrip("/")
        self.prefix = prefix.strip("/")

    @classmethod
    def from_env(cls, env: Any) -> "ImageStorageEngine":
        bucket = getattr(env, cls.DEFAULT_BINDING, None)
        public_base_url = getattr(env, "MIKO_MEDIA_PUBLIC_URL", None)

        return cls(
            bucket,
            public_base_url=public_base_url,
        )

    @staticmethod
    def parse_data_uri(data_uri: str) -> tuple[bytes, str, str]:
        """
        Parse a base64 image data URI.

        Returns:
            (raw_bytes, mime_type, extension)
        """
        if not isinstance(data_uri, str):
            raise ImageDataError("reference_image must be a string.")

        value = data_uri.strip()
        match = ImageStorageEngine.DATA_URI_RE.match(value)

        if not match:
            raise ImageDataError(
                "Invalid image data URI. Expected "
                "'data:image/<type>;base64,<data>'."
            )

        mime = match.group("mime").lower()
        encoded = re.sub(r"\s+", "", match.group("data"))

        try:
            raw = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ImageDataError(
                "Image base64 data is invalid."
            ) from exc

        if not raw:
            raise ImageDataError("Image data is empty.")

        extension_map = {
            "image/png": "png",
            "image/jpeg": "jpg",
            "image/jpg": "jpg",
            "image/webp": "webp",
            "image/gif": "gif",
        }

        extension = extension_map.get(mime)
        if not extension:
            raise ImageDataError(
                f"Unsupported image MIME type: {mime}. "
                "Supported: PNG, JPEG, WebP, GIF."
            )

        return raw, mime, extension

    @staticmethod
    def _safe_scene(scene_number: Optional[int]) -> str:
        if scene_number is None:
            return "scene"
        try:
            value = int(scene_number)
        except (TypeError, ValueError) as exc:
            raise ImageDataError("scene_number must be an integer.") from exc

        if value < 1 or value > 999:
            raise ImageDataError("scene_number must be between 1 and 999.")

        return f"scene-{value:02d}"

    def build_key(
        self,
        *,
        episode_id: Optional[str] = None,
        scene_number: Optional[int] = None,
        extension: str = "png",
    ) -> str:
        """
        Build a collision-resistant object key.

        Example:
            miko/images/episode-abc/scene-01-<uuid>.png
        """
        episode = (episode_id or "episode").strip()

        # Keep only URL/path-safe characters.
        episode = re.sub(r"[^A-Za-z0-9._-]+", "-", episode)
        episode = episode[:80] or "episode"

        scene = self._safe_scene(scene_number)
        token = uuid.uuid4().hex[:16]
        timestamp = int(time.time())

        return (
            f"{self.prefix}/{episode}/"
            f"{scene}-{timestamp}-{token}.{extension}"
        )

    def build_public_url(self, key: str) -> Optional[str]:
        if not self.public_base_url:
            return None

        clean_key = key.lstrip("/")
        return f"{self.public_base_url}/{clean_key}"

    async def upload_bytes(
        self,
        data: bytes,
        *,
        mime_type: str = "image/png",
        key: str,
        episode_id: Optional[str] = None,
        scene_number: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Upload raw image bytes to R2.

        R2's Workers API is accessed through the binding, so no R2
        API token is required inside the Worker.
        """
        if not isinstance(data, bytes):
            raise ImageDataError("data must be bytes.")

        if not data:
            raise ImageDataError("Image data is empty.")

        key = key.strip().lstrip("/")
        if not key:
            raise ImageDataError("R2 object key is empty.")

        mime_type = (mime_type or "application/octet-stream").strip().lower()

        # Workers Python FFI can pass Python bytes to JS APIs, but an
        # explicit bytearray keeps the payload unambiguous for the R2
        # binding in Pyodide.
        payload = bytearray(data)

        await self.bucket.put(
            key,
            payload,
            {
                "httpMetadata": {
                    "contentType": mime_type,
                    "cacheControl": "public, max-age=31536000, immutable",
                }
            },
        )

        return {
            "success": True,
            "provider": "cloudflare-r2",
            "key": key,
            "mime_type": mime_type,
            "size_bytes": len(data),
            "public_url": self.build_public_url(key),
            "episode_id": episode_id,
            "scene_number": scene_number,
        }

    async def upload_data_uri(
        self,
        data_uri: str,
        *,
        episode_id: Optional[str] = None,
        scene_number: Optional[int] = None,
        key: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Decode a browser data URI and upload it to R2.
        """
        raw, mime, extension = self.parse_data_uri(data_uri)

        object_key = key or self.build_key(
            episode_id=episode_id,
            scene_number=scene_number,
            extension=extension,
        )

        return await self.upload_bytes(
            raw,
            mime_type=mime,
            key=object_key,
            episode_id=episode_id,
            scene_number=scene_number,
        )

    async def head(self, key: str) -> dict[str, Any]:
        """Check whether an object exists and return basic metadata."""
        key = key.strip().lstrip("/")
        if not key:
            raise ImageDataError("R2 object key is empty.")

        obj = await self.bucket.head(key)

        if obj is None:
            return {
                "success": False,
                "exists": False,
                "key": key,
            }

        return {
            "success": True,
            "exists": True,
            "key": key,
            "size": getattr(obj, "size", None),
            "etag": getattr(obj, "etag", None),
            "http_etag": getattr(obj, "httpEtag", None),
            "uploaded": getattr(obj, "uploaded", None),
            "http_metadata": getattr(obj, "httpMetadata", None),
            "public_url": self.build_public_url(key),
        }

    async def delete(self, key: str) -> dict[str, Any]:
        """Delete an image from R2."""
        key = key.strip().lstrip("/")
        if not key:
            raise ImageDataError("R2 object key is empty.")

        await self.bucket.delete(key)

        return {
            "success": True,
            "provider": "cloudflare-r2",
            "key": key,
            "deleted": True,
        }


__all__ = [
    "ImageStorageEngine",
    "ImageStorageError",
    "ImageDataError",
    "ImageStorageConfigurationError",
]
