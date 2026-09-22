"""
Prompt data models for Miko AI Shorts.

Dependency-free dataclasses so these models can be used by the local backend,
tests, and future provider adapters without locking the project to one AI SDK.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PromptRequest:
    episode_id: str
    scene_number: int
    language: str = "id"
    include_character_lock: bool = True
    include_world_lock: bool = True
    include_negative_prompt: bool = True
    extra_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImagePrompt:
    episode_id: str
    scene_number: int
    prompt: str
    negative_prompt: str
    aspect_ratio: str = "9:16"
    resolution: str = "1080x1920"
    style: str = "polished stylized 3D children's animation"
    character_lock: str = ""
    world_lock: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "scene_number": self.scene_number,
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "aspect_ratio": self.aspect_ratio,
            "resolution": self.resolution,
            "style": self.style,
            "character_lock": self.character_lock,
            "world_lock": self.world_lock,
            "metadata": self.metadata,
        }


@dataclass
class VideoPrompt:
    episode_id: str
    scene_number: int
    prompt: str
    duration_seconds: int
    aspect_ratio: str = "9:16"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "scene_number": self.scene_number,
            "prompt": self.prompt,
            "duration_seconds": self.duration_seconds,
            "aspect_ratio": self.aspect_ratio,
            "metadata": self.metadata,
        }
