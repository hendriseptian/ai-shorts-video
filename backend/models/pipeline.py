"""
Pipeline state models for an episode.

The state machine is intentionally simple and deterministic so failed stages
can be retried without regenerating successful previous stages.
"""

from dataclasses import dataclass, field
from typing import Any


PIPELINE_STATES = (
    "DRAFT",
    "STORY_GENERATED",
    "SCENES_GENERATED",
    "PROMPTS_GENERATED",
    "IMAGES_GENERATED",
    "VIDEOS_GENERATED",
    "VOICE_GENERATED",
    "EDITED",
    "QC_PASSED",
    "READY_TO_UPLOAD",
    "UPLOADED",
    "FAILED",
)


@dataclass
class PipelineManifest:
    episode_id: str
    status: str = "DRAFT"
    story: bool = False
    scenes: bool = False
    image_prompts: bool = False
    images: bool = False
    videos: bool = False
    voice: bool = False
    edit: bool = False
    qc: bool = False
    youtube: bool = False
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def set_stage(self, stage: str, completed: bool = True) -> None:
        mapping = {
            "story": "story",
            "scenes": "scenes",
            "prompts": "image_prompts",
            "images": "images",
            "videos": "videos",
            "voice": "voice",
            "edit": "edit",
            "qc": "qc",
            "youtube": "youtube",
        }

        if stage not in mapping:
            raise ValueError(f"Unknown pipeline stage: {stage}")

        setattr(self, mapping[stage], completed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "status": self.status,
            "story": self.story,
            "scenes": self.scenes,
            "image_prompts": self.image_prompts,
            "images": self.images,
            "videos": self.videos,
            "voice": self.voice,
            "edit": self.edit,
            "qc": self.qc,
            "youtube": self.youtube,
            "error": self.error,
            "metadata": self.metadata,
        }
