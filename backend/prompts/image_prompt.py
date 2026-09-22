"""
Scene-to-image prompt builder for Miko AI Shorts.

This version is provider-neutral and deterministic. It prepares a structured
prompt that can later be sent to Gemini, Cloudflare, or another image provider.
"""

from __future__ import annotations

from typing import Any

from models.prompt import ImagePrompt, PromptRequest
from prompts.negative_prompt import build_negative_prompt


CHARACTER_LOCK = (
    "Miko is a cute 3D animated male kitten, age impression 4–6, "
    "small adorable orange-and-white kitten with a slightly oversized round head, "
    "small body, short legs, fluffy tail, expressive large dark-brown eyes, "
    "white muzzle, cheeks, chest, belly, paws and tail tip, fluffy orange fur, "
    "wearing a bright blue hoodie with white drawstrings and a small round paw pendant, "
    "no shoes, soft pink paw pads. Keep Miko's proportions, fur pattern, face, eyes, "
    "hoodie and colors identical across every scene."
)

STYLE_LOCK = (
    "polished stylized 3D children's animation, rounded proportions, soft fluffy fur, "
    "expressive animation, bright warm lighting, wholesome family-friendly atmosphere, "
    "clean cinematic composition, detailed but non-distracting background, vertical 9:16"
)


def _value(scene: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        value = scene.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def build_image_prompt(
    scene: dict[str, Any],
    episode_id: str = "UNSPECIFIED",
    language: str = "id",
    include_character_lock: bool = True,
) -> ImagePrompt:
    scene_number = int(scene.get("scene_number", 1))
    phase = _value(scene, "phase", default=f"Scene {scene_number}")
    story = _value(scene, "story", "action", default="Miko is in the scene.")
    emotion = _value(scene, "emotion", default="cheerful")

    location = _value(scene, "location", "setting", default="a bright wholesome Miko world")
    characters = _value(scene, "characters", "character", default="Miko")
    object_value = _value(scene, "main_object", "object", default="")

    parts = [
        "Create a single vertical children's animation frame.",
        f"Scene phase: {phase}.",
        f"Scene action: {story}.",
        f"Emotion: {emotion}.",
        f"Location: {location}.",
        f"Characters: {characters}.",
    ]

    if object_value:
        parts.append(f"Important object: {object_value}.")

    if include_character_lock:
        parts.append(f"Character consistency lock: {CHARACTER_LOCK}")

    parts.append(f"Visual style lock: {STYLE_LOCK}")

    prompt = " ".join(parts)

    return ImagePrompt(
        episode_id=episode_id,
        scene_number=scene_number,
        prompt=prompt,
        negative_prompt=build_negative_prompt(),
        character_lock=CHARACTER_LOCK if include_character_lock else "",
        world_lock=location,
        metadata={
            "language": language,
            "source_phase": phase,
            "provider_neutral": True,
        },
    )


def build_scene_image_prompts(
    scenes: list[dict[str, Any]],
    episode_id: str = "UNSPECIFIED",
    language: str = "id",
) -> list[ImagePrompt]:
    return [
        build_image_prompt(
            scene,
            episode_id=episode_id,
            language=language,
            include_character_lock=True,
        )
        for scene in scenes
    ]
