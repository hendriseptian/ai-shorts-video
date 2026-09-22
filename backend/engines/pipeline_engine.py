"""
Lightweight pipeline controller.

This module tracks stage state only. It intentionally does not call external
AI/media providers yet. That keeps the current story system stable while
preparing the project for the full production pipeline.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from models.pipeline import PIPELINE_STATES, PipelineManifest


STAGE_TO_STATUS = {
    "story": "STORY_GENERATED",
    "scenes": "SCENES_GENERATED",
    "prompts": "PROMPTS_GENERATED",
    "images": "IMAGES_GENERATED",
    "videos": "VIDEOS_GENERATED",
    "voice": "VOICE_GENERATED",
    "edit": "EDITED",
    "qc": "QC_PASSED",
    "youtube": "UPLOADED",
}


class PipelineEngine:
    def __init__(self) -> None:
        self._manifests: dict[str, PipelineManifest] = {}

    def create(self, episode_id: str) -> PipelineManifest:
        episode_id = str(episode_id).strip()

        if not episode_id:
            raise ValueError("episode_id is required.")

        manifest = PipelineManifest(episode_id=episode_id)
        self._manifests[episode_id] = manifest
        return manifest

    def get(self, episode_id: str) -> PipelineManifest | None:
        return self._manifests.get(str(episode_id).strip())

    def update_stage(
        self,
        episode_id: str,
        stage: str,
        *,
        completed: bool = True,
        error: str | None = None,
    ) -> PipelineManifest:
        manifest = self.get(episode_id)

        if manifest is None:
            manifest = self.create(episode_id)

        stage = str(stage).strip().lower()

        if stage not in STAGE_TO_STATUS:
            raise ValueError(
                f"Unknown stage '{stage}'. "
                f"Allowed: {', '.join(STAGE_TO_STATUS)}"
            )

        manifest.set_stage(stage, completed=completed)
        manifest.error = error

        if error:
            manifest.status = "FAILED"
        elif completed:
            manifest.status = STAGE_TO_STATUS[stage]

        return manifest

    def status(self, episode_id: str) -> dict[str, Any]:
        manifest = self.get(episode_id)

        if manifest is None:
            return {
                "episode_id": episode_id,
                "status": "NOT_FOUND",
                "exists": False,
            }

        return {
            "episode_id": episode_id,
            "status": manifest.status,
            "exists": True,
            "manifest": manifest.to_dict(),
        }

    def reset(self, episode_id: str) -> PipelineManifest:
        manifest = self.create(episode_id)
        return manifest

    @staticmethod
    def allowed_states() -> tuple[str, ...]:
        return PIPELINE_STATES
