"""
Miko character consistency guard.

This module does not generate images. It validates and reinforces the canonical
Miko description before a scene prompt reaches an image provider.
"""

from __future__ import annotations

import re
from typing import Any


MIKO_CANONICAL = {
    "species": "orange-and-white kitten",
    "gender": "male",
    "age_impression": "4–6",
    "eyes": "large dark-brown eyes",
    "fur": "fluffy orange fur",
    "white_markings": "white muzzle, cheeks, chest, belly, paws and tail tip",
    "clothing": "bright blue hoodie with white drawstrings and a small round paw pendant",
    "shoes": "no shoes",
    "body": "slightly oversized round head, small body, short legs, fluffy tail",
    "style": "polished stylized 3D children's animation",
}


REQUIRED_PHRASES = (
    "orange-and-white kitten",
    "large dark-brown eyes",
    "fluffy orange fur",
    "bright blue hoodie",
)


def canonical_character_prompt() -> str:
    return (
        "Miko, a cute 3D animated male kitten, age impression 4–6, "
        "orange-and-white kitten with a slightly oversized round head, small body, "
        "short legs, fluffy tail, large dark-brown eyes, white muzzle, cheeks, chest, "
        "belly, paws and tail tip, fluffy orange fur, wearing a bright blue hoodie "
        "with white drawstrings and a small round paw pendant, no shoes."
    )


def validate_character_text(text: str) -> list[str]:
    """Return consistency warnings; an empty list means no warning."""
    source = str(text or "").lower()
    warnings: list[str] = []

    for phrase in REQUIRED_PHRASES:
        if phrase.lower() not in source:
            warnings.append(f"Missing canonical character phrase: {phrase}")

    forbidden = {
        "brown kitten": "brown kitten",
        "red hoodie": "red hoodie",
        "red shirt": "red shirt",
        "shoes": "shoes",
        "human hair": "human hair",
    }

    for needle, label in forbidden.items():
        if re.search(rf"\b{re.escape(needle)}\b", source):
            warnings.append(f"Potential character inconsistency: {label}")

    return warnings


def enforce_character_consistency(
    prompt: str,
    *,
    strict: bool = False,
) -> str:
    warnings = validate_character_text(prompt)

    if strict and warnings:
        raise ValueError("; ".join(warnings))

    canonical = canonical_character_prompt()

    if canonical.lower() not in str(prompt).lower():
        return f"{prompt.strip()} Character consistency lock: {canonical}"

    return prompt


def validate_scene(scene: dict[str, Any], *, strict: bool = False) -> dict[str, Any]:
    """
    Validate a scene and return a copy with consistency metadata.
    """
    result = dict(scene)

    combined = " ".join(
        str(result.get(key, ""))
        for key in ("story", "action", "dialogue", "characters", "visual_prompt")
    )

    warnings = validate_character_text(combined)

    if strict and warnings:
        raise ValueError(
            f"Scene {result.get('scene_number', '?')} failed character consistency: "
            + "; ".join(warnings)
        )

    result["character_consistency"] = {
        "status": "pass" if not warnings else "warning",
        "warnings": warnings,
        "canonical_character": MIKO_CANONICAL,
    }

    return result
