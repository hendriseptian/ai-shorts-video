"""
Cloudflare-compatible Image Prompt Engine V1.

This module is intentionally self-contained so the Python Worker does not need
filesystem access, package-data files, or imports from the local backend tree.
It converts the current Story Engine response into deterministic visual prompts.
"""

from __future__ import annotations

from typing import Any


class ImagePromptEngineError(Exception):
    """Image prompt generation error."""


class ImagePromptEngine:
    name = "image-prompt-engine"
    version = "1.0.0"

    CHARACTER_LOCK = (
        "Miko is a cute 3D animated male kitten, age impression 4–6, "
        "small adorable orange-and-white kitten with a slightly oversized round head, "
        "small body, short legs, fluffy tail, expressive large dark-brown eyes, "
        "white muzzle, cheeks, chest, belly, paws and tail tip, fluffy orange fur, "
        "wearing a bright blue hoodie with white drawstrings and a small round paw "
        "pendant, no shoes, soft pink paw pads. Keep Miko's proportions, fur pattern, "
        "face, eyes, hoodie and colors identical across every scene."
    )

    STYLE_LOCK = (
        "polished stylized 3D children's animation, rounded proportions, soft fluffy fur, "
        "expressive animation, bright warm lighting, wholesome family-friendly atmosphere, "
        "clean cinematic composition, detailed but non-distracting background, vertical 9:16"
    )

    NEGATIVE_PROMPT = (
        "violence, fighting, weapons, blood, injury, horror, gore, frightening scene, "
        "scary monster, dark horror lighting, dangerous imitation, dangerous challenge, "
        "adult themes, sexual content, politics, religious debate, hate, discrimination, "
        "inappropriate language, profanity, disturbing imagery, death as a central theme, "
        "cruelty to animals, dangerous prank, realistic human child, human hair on Miko, "
        "shoes on Miko, clothing other than the blue hoodie, inconsistent character design"
    )

    WORLD_LOCKS = {
        "MIKOS_HOUSE": (
            "cozy cream-colored walls, blue door, round windows, red-orange roof, "
            "small cheerful yard with flowers, safe cozy family atmosphere"
        ),
        "RAINBOW_PARK": (
            "bright green grass, large friendly tree, colorful flowers, bench, path, "
            "swing, slide, small pond, butterflies and birds, sunny cheerful atmosphere"
        ),
        "SUNNY_FOREST": (
            "bright safe forest, green trees, flowers, mushrooms, bushes, friendly rocks, "
            "small clear stream, birds, rabbits and butterflies, never dark or frightening"
        ),
        "SUNNY_BEACH": (
            "warm sandy beach, clear blue sea, shells, smooth rocks, colorful umbrella, "
            "bucket, beach ball and a small boat, bright sunny family atmosphere"
        ),
        "LITTLE_SCHOOL": (
            "bright friendly classroom, board, small desks and chairs, bookshelf, "
            "schoolyard and garden, cheerful educational atmosphere"
        ),
        "PLAYGROUND": (
            "colorful safe playground with slide, swing, climbing structure, sandbox, "
            "balls and jungle gym, bright cheerful surroundings"
        ),
        "FLOWER_GARDEN": (
            "beautiful garden with sunflowers, tulips, daisies and lavender, "
            "butterflies and friendly bees, warm daylight"
        ),
        "LITTLE_FARM": (
            "small cheerful farm with chicken coop, cows, goats, rabbits, vegetable garden "
            "and friendly barn, bright countryside atmosphere"
        ),
        "CLOUD_HILL": (
            "soft green hill under a bright sky, distant views, fluffy animal-shaped clouds, "
            "gentle imaginative fantasy atmosphere"
        ),
        "MIKOS_NIGHT_GARDEN": (
            "calm cozy garden at night with moon, stars, softly glowing flowers and fireflies, "
            "magical but never scary"
        ),
    }

    @staticmethod
    def _value(scene: dict[str, Any], *keys: str, default: str = "") -> str:
        for key in keys:
            value = scene.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return default

    @classmethod
    def _world_lock(cls, location: str) -> str:
        value = str(location or "").strip()
        normalized = value.upper().replace(" ", "_").replace("'", "")
        return cls.WORLD_LOCKS.get(
            value,
            cls.WORLD_LOCKS.get(
                normalized,
                "bright, warm, cheerful and safe Miko world, detailed but "
                "non-distracting background, family-friendly atmosphere",
            ),
        )

    @classmethod
    def _character_consistency(cls, prompt: str) -> str:
        required = (
            "orange-and-white kitten",
            "large dark-brown eyes",
            "fluffy orange fur",
            "bright blue hoodie",
        )
        lower = prompt.lower()

        if all(item in lower for item in required):
            return prompt

        return f"{prompt} Character consistency lock: {cls.CHARACTER_LOCK}"

    def generate_for_scene(
        self,
        scene: dict[str, Any],
        *,
        episode_id: str,
        language: str,
        episode_location: str | None = None,
    ) -> dict[str, Any]:
        if not isinstance(scene, dict):
            raise ImagePromptEngineError("Each scene must be an object.")

        scene_number = int(scene.get("scene_number", 1))
        phase = self._value(
            scene, "phase", default=f"Scene {scene_number}"
        )
        story = self._value(
            scene, "story", "action",
            default="Miko is in the scene.",
        )
        emotion = self._value(
            scene, "emotion", default="cheerful"
        )
        location = self._value(
            scene, "location", "setting",
            default=episode_location or "Miko's world",
        )
        characters = self._value(
            scene, "characters", "character", default="Miko"
        )
        main_object = self._value(
            scene, "main_object", "object", default=""
        )
        dialogue = self._value(scene, "dialogue", default="")

        world_lock = self._world_lock(location)

        parts = [
            "Create a single vertical children's animation frame.",
            f"Scene phase: {phase}.",
            f"Scene action: {story}.",
            f"Emotion: {emotion}.",
            f"Location: {location}.",
            f"Characters: {characters}.",
        ]

        if main_object:
            parts.append(f"Important object: {main_object}.")

        if dialogue:
            parts.append(
                "Dialogue context should be reflected through the character's "
                "expression and body language, without adding written text to the image."
            )

        parts.append(f"Character consistency lock: {self.CHARACTER_LOCK}")
        parts.append(f"Recurring world visual lock: {world_lock}.")
        parts.append(f"Visual style lock: {self.STYLE_LOCK}.")

        prompt = self._character_consistency(" ".join(parts))

        return {
            "episode_id": episode_id,
            "scene_number": scene_number,
            "prompt": prompt,
            "negative_prompt": self.NEGATIVE_PROMPT,
            "aspect_ratio": "9:16",
            "resolution": "1080x1920",
            "style": "polished stylized 3D children's animation",
            "character_lock": self.CHARACTER_LOCK,
            "world_lock": world_lock,
            "metadata": {
                "language": language,
                "engine": self.name,
                "engine_version": self.version,
                "provider_neutral": True,
            },
        }

    def generate_for_story(self, story: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(story, dict):
            raise ImagePromptEngineError("Story must be an object.")

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

        prompts = [
            self.generate_for_scene(
                scene,
                episode_id=episode_id,
                language=language,
                episode_location=episode_location,
            )
            for scene in scenes
        ]

        return {
            "success": True,
            "engine": self.name,
            "version": self.version,
            "episode_id": episode_id,
            "language": language,
            "scene_count": len(prompts),
            "prompts": prompts,
        }
