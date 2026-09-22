"""
Image Prompt Engine V1.

Converts an already-generated Miko story into deterministic visual prompts.
This engine does not call an AI provider yet.

It accepts the current Story Engine response and produces one image prompt
per scene, including Miko character consistency and recurring world/location
visual locks.
"""

from __future__ import annotations

from typing import Any

from engines.character_consistency import enforce_character_consistency
from models.prompt import ImagePrompt
from prompts.image_prompt import build_image_prompt
from prompts.world_prompt import get_world_lock


class ImagePromptEngineError(Exception):
    """Base exception for image prompt generation."""


class ImagePromptEngine:
    name = "image_prompt_engine"
    version = "1.1.0"

    def generate_for_scene(
        self,
        scene: dict[str, Any],
        *,
        episode_id: str = "UNSPECIFIED",
        language: str = "id",
        episode_location: str | None = None,
    ) -> ImagePrompt:
        if not isinstance(scene, dict):
            raise ImagePromptEngineError("Scene must be an object/dictionary.")

        location = (
            scene.get("location")
            or scene.get("setting")
            or episode_location
            or ""
        )

        scene_for_prompt = dict(scene)
        scene_for_prompt["location"] = location

        prompt = build_image_prompt(
            scene_for_prompt,
            episode_id=episode_id,
            language=language,
            include_character_lock=True,
        )

        world_lock = get_world_lock(location)

        prompt.world_lock = world_lock
        prompt.prompt = (
            f"{prompt.prompt} "
            f"Recurring world visual lock: {world_lock}."
        )
        prompt.prompt = enforce_character_consistency(prompt.prompt)

        prompt.metadata.update({
            "engine": self.name,
            "engine_version": self.version,
            "world_lock_id": str(location),
        })

        return prompt

    def generate_for_story(
        self,
        story: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(story, dict):
            raise ImagePromptEngineError("Story must be an object/dictionary.")

        scenes = story.get("scenes")

        if not isinstance(scenes, list) or not scenes:
            raise ImagePromptEngineError(
                "Story does not contain a valid non-empty 'scenes' list."
            )

        episode = story.get("episode") or {}
        episode_id = str(
            episode.get("episode_id")
            or story.get("episode_id")
            or "UNSPECIFIED"
        )
        language = str(
            episode.get("language")
            or story.get("language")
            or "id"
        )
        episode_location = (
            episode.get("location")
            or story.get("location")
            or None
        )

        prompts: list[dict[str, Any]] = []

        for scene in scenes:
            image_prompt = self.generate_for_scene(
                scene,
                episode_id=episode_id,
                language=language,
                episode_location=episode_location,
            )
            prompts.append(image_prompt.to_dict())

        return {
            "success": True,
            "engine": self.name,
            "version": self.version,
            "episode_id": episode_id,
            "language": language,
            "scene_count": len(prompts),
            "prompts": prompts,
        }


def generate_image_prompts(story: dict[str, Any]) -> dict[str, Any]:
    return ImagePromptEngine().generate_for_story(story)
