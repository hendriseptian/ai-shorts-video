"""
Media asset models.

These models describe generated media without assuming where the media is stored.
The actual provider/storage implementation can be added later.
"""

from dataclasses import dataclass, field
from typing import Any, Literal


MediaType = Literal["image", "video", "audio", "subtitle", "final_video"]
MediaStatus = Literal["pending", "processing", "ready", "failed"]


@dataclass
class MediaAsset:
    episode_id: str
    media_type: MediaType
    status: MediaStatus = "pending"
    scene_number: int | None = None
    provider: str | None = None
    url: str | None = None
    storage_key: str | None = None
    local_path: str | None = None
    duration_seconds: float | None = None
    width: int | None = None
    height: int | None = None
    mime_type: str | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "media_type": self.media_type,
            "status": self.status,
            "scene_number": self.scene_number,
            "provider": self.provider,
            "url": self.url,
            "storage_key": self.storage_key,
            "local_path": self.local_path,
            "duration_seconds": self.duration_seconds,
            "width": self.width,
            "height": self.height,
            "mime_type": self.mime_type,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class SceneMedia:
    scene_number: int
    image: MediaAsset | None = None
    video: MediaAsset | None = None
    voice: MediaAsset | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_number": self.scene_number,
            "image": self.image.to_dict() if self.image else None,
            "video": self.video.to_dict() if self.video else None,
            "voice": self.voice.to_dict() if self.voice else None,
        }
