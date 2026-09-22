from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from .bibles import CHARACTER_BIBLE, STORY_BIBLE, WORLD_BIBLE


class StoryEngineError(Exception):
    """Base exception for Story Engine."""


class BibleLoadError(StoryEngineError):
    """Compatibility exception retained for the V1 API."""


class StoryValidationError(StoryEngineError):
    """Raised when generated story fails validation."""


class BibleLoader:
    """
    Cloudflare-safe Bible loader.

    There is intentionally no filesystem, Path, JSON file, importlib.resources,
    or environment-file dependency here. Bible data lives in bibles.py.
    """

    def load_all(self) -> Dict[str, Dict[str, Any]]:
        return {
            "character": CHARACTER_BIBLE,
            "story": STORY_BIBLE,
            "world": WORLD_BIBLE,
        }


class StoryEngine:
    """Generate and validate structured Miko Shorts stories."""

    def __init__(self, bible_loader: Optional[BibleLoader] = None):
        self.bible_loader = bible_loader or BibleLoader()
        self.bibles = self.bible_loader.load_all()

        self.character_bible = self.bibles["character"]
        self.story_bible = self.bibles["story"]
        self.world_bible = self.bibles["world"]

    def generate_story(
        self,
        category: Optional[str] = None,
        core_value: Optional[str] = None,
        location: Optional[str] = None,
        supporting_character: Optional[str] = None,
        main_object: Optional[str] = None,
        duration: Optional[int] = None,
        language: str = "id",
        episode_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        category = self._select_category(category)
        core_value = self._select_core_value(core_value)
        location = self._select_location(location)
        supporting_character = self._select_supporting_character(
            supporting_character
        )

        duration = int(duration or self._get_default_duration())
        if duration < 10 or duration > 180:
            raise StoryEngineError("Duration must be between 10 and 180 seconds.")

        episode_id = episode_id or self._generate_episode_id()

        story = self._build_story(
            episode_id=episode_id,
            category=category,
            core_value=core_value,
            location=location,
            supporting_character=supporting_character,
            main_object=main_object,
            duration=duration,
            language=language,
        )

        self.validate_story(story)
        return story

    def _select_category(self, category: Optional[str]) -> str:
        categories = self.story_bible["categories"]
        if category:
            value = category.upper().strip()
            if value not in categories:
                raise StoryEngineError(f"Unknown story category: {value}")
            return value
        return random.choice(categories)

    def _select_core_value(self, core_value: Optional[str]) -> str:
        values = self.story_bible["core_values"]
        if core_value:
            value = core_value.upper().strip()
            if value not in values:
                raise StoryEngineError(f"Unknown core value: {value}")
            return value
        return random.choice(values)

    def _select_location(self, location: Optional[str]) -> str:
        locations = self.world_bible["locations"]
        location_map = {item["id"]: item for item in locations}

        if location:
            value = location.upper().strip()
            if value not in location_map:
                raise StoryEngineError(f"Unknown location: {value}")
            return value

        weighted: List[str] = []
        for item in locations:
            location_id = item["id"]
            weight = 3 if item.get("frequency") == "most_frequently_used" else 1
            weighted.extend([location_id] * weight)

        return random.choice(weighted)

    def _select_supporting_character(
        self,
        supporting_character: Optional[str],
    ) -> Optional[str]:
        characters = self.character_bible["supporting_characters"]
        character_map = {item["id"]: item for item in characters}

        if supporting_character:
            value = supporting_character.upper().strip()
            if value not in character_map:
                raise StoryEngineError(
                    f"Unknown supporting character: {value}"
                )
            return value

        # 25% of episodes can be Miko-only.
        if random.random() < 0.25:
            return None

        return random.choice(list(character_map.keys()))

    def _get_default_duration(self) -> int:
        return int(
            self.story_bible["story_identity"]["default_duration_seconds"]
        )

    def _generate_episode_id(self) -> str:
        return f"MIKO-{random.randint(1, 999999):06d}"

    def _get_location(self, location_id: str) -> Dict[str, Any]:
        for location in self.world_bible["locations"]:
            if location["id"] == location_id:
                return location
        raise StoryEngineError(f"Location not found: {location_id}")

    def _get_supporting_character(
        self,
        character_id: str,
    ) -> Dict[str, Any]:
        for character in self.character_bible["supporting_characters"]:
            if character["id"] == character_id:
                return character
        raise StoryEngineError(
            f"Supporting character not found: {character_id}"
        )

    def _suggest_object(self, location: str) -> str:
        objects = {
            "MIKOS_HOUSE": [
                "STORY_BOOK", "CRAYONS", "TEDDY_BEAR", "BALLOON"
            ],
            "RAINBOW_PARK": [
                "RAINBOW", "BALL", "SOAP_BUBBLES", "BUTTERFLY"
            ],
            "SUNNY_FOREST": [
                "RAINBOW", "LITTLE_STREAM", "MUSHROOM",
                "FEATHER", "BUTTERFLY"
            ],
            "SUNNY_BEACH": [
                "SEASHELL", "BEACH_BALL", "SMALL_BOAT",
                "COLORFUL_UMBRELLA"
            ],
            "LITTLE_SCHOOL": [
                "CRAYONS", "SHAPE_BLOCKS", "STORY_BOOK", "COLOR_CARDS"
            ],
            "PLAYGROUND": [
                "BALL", "SOAP_BUBBLES", "BALLOON"
            ],
            "FLOWER_GARDEN": [
                "SUNFLOWER", "WATERING_CAN", "BUTTERFLY", "LITTLE_BEE"
            ],
            "LITTLE_FARM": [
                "CARROT", "WATERING_CAN", "BASKET", "FEATHER"
            ],
            "CLOUD_HILL": [
                "ANIMAL_SHAPED_CLOUD", "RAINBOW", "FALLING_STAR"
            ],
            "MIKOS_NIGHT_GARDEN": [
                "FIREFLY", "GLOWING_FLOWER", "STAR", "MOON"
            ],
        }
        return random.choice(objects.get(location, ["COLORFUL_TOY"]))

    @staticmethod
    def _display(value: str) -> str:
        return value.replace("_", " ").lower()

    def _generate_title(
        self,
        main_object: str,
    ) -> str:
        object_name = self._display(main_object).title()
        return random.choice(
            [
                f"Miko Menemukan {object_name}!",
                f"Miko dan {object_name}",
                f"Petualangan Miko: {object_name}",
                f"Miko Penasaran dengan {object_name}",
            ]
        )

    def _generate_hook(
        self,
        location: Dict[str, Any],
        main_object: str,
    ) -> str:
        return (
            f"Miko melihat sesuatu yang menarik di "
            f"{location['name']}: {self._display(main_object)}!"
        )

    def _generate_lesson(self, core_value: str) -> str:
        lessons = {
            "KINDNESS": "Berbuat baik kepada orang lain membuat suasana menjadi lebih bahagia.",
            "SHARING": "Berbagi membuat bermain dan belajar menjadi lebih menyenangkan.",
            "HONESTY": "Berkata jujur membantu kita menyelesaikan masalah dengan baik.",
            "COURAGE": "Berani mencoba membantu kita menemukan hal baru.",
            "PATIENCE": "Bersabar membantu kita menyelesaikan sesuatu dengan lebih baik.",
            "CURIOSITY": "Rasa ingin tahu membantu kita belajar menemukan hal baru.",
            "HELPING_OTHERS": "Membantu orang lain adalah hal baik yang membuat kita merasa bahagia.",
            "RESPECT": "Menghargai orang lain membuat kita bisa bermain dan belajar bersama.",
            "CLEANLINESS": "Menjaga kebersihan membuat lingkungan menjadi nyaman.",
            "TEAMWORK": "Bekerja bersama membuat masalah terasa lebih mudah.",
            "PROBLEM_SOLVING": "Berpikir tenang membantu kita menemukan solusi.",
            "LEARNING_FROM_MISTAKES": "Kesalahan bisa menjadi kesempatan untuk belajar.",
            "RESPONSIBILITY": "Merawat sesuatu dengan baik adalah bentuk tanggung jawab.",
            "EMPATHY": "Memahami perasaan orang lain membantu kita menjadi teman yang baik.",
            "GRATITUDE": "Menghargai hal-hal kecil membuat kita merasa lebih bahagia.",
            "SELF_CONFIDENCE": "Percaya pada diri sendiri membantu kita berani mencoba.",
            "TAKING_CARE_OF_NATURE": "Menjaga alam membantu lingkungan tetap indah dan nyaman.",
        }
        return lessons.get(
            core_value,
            "Setiap pengalaman bisa menjadi kesempatan untuk belajar.",
        )

    def _build_scenes(
        self,
        core_value: str,
        location_data: Dict[str, Any],
        supporting_data: Optional[Dict[str, Any]],
        main_object: str,
        duration: int,
    ) -> List[Dict[str, Any]]:
        standard = [5, 10, 20, 15, 10]

        if duration < 5:
            raise StoryEngineError(
                "Duration must be at least 5 seconds for the five-scene structure."
            )

        # Preserve the 5/10/20/15/10 story rhythm while guaranteeing
        # an exact total duration.
        raw = [max(1, round(x * duration / 60)) for x in standard]
        difference = duration - sum(raw)
        raw[-1] += difference

        if raw[-1] < 1:
            # Fallback for very short durations.
            raw = [1, 1, 1, 1, duration - 4]

        object_name = self._display(main_object)
        location_name = location_data["name"]
        supporting_name = supporting_data["name"] if supporting_data else None
        value_name = self._display(core_value)

        scenes = [
            {
                "scene_number": 1,
                "duration": raw[0],
                "phase": "MIKO_SEES",
                "story": (
                    f"Miko berada di {location_name} ketika melihat "
                    f"{object_name}."
                ),
                "action": (
                    f"Miko berhenti dan memperhatikan {object_name} "
                    "dengan rasa ingin tahu."
                ),
                "dialogue": '"Wah, itu apa ya?"',
                "emotion": "curious",
            },
            {
                "scene_number": 2,
                "duration": raw[1],
                "phase": "MIKO_DISCOVERS",
                "story": (
                    f"Miko mendekati {object_name} untuk melihatnya "
                    "lebih dekat."
                ),
                "action": (
                    f"Miko mengamati {object_name} dari beberapa sisi "
                    "dan menemukan sesuatu yang menarik."
                ),
                "dialogue": f'"Ohh... ternyata {object_name}!"',
                "emotion": "excited",
            },
            {
                "scene_number": 3,
                "duration": raw[2],
                "phase": "MIKO_PLAYS_TRIES_EXPLORES",
                "story": (
                    f"Miko mencoba berinteraksi dengan {object_name} "
                    "dengan cara yang aman."
                ),
                "action": (
                    f"Miko bermain atau mengeksplorasi {object_name} "
                    "sambil belajar."
                ),
                "dialogue": '"Aku coba!"',
                "emotion": "playful",
            },
            {
                "scene_number": 4,
                "duration": raw[3],
                "phase": "SOMETHING_HAPPENS",
                "story": (
                    f"Terjadi kejadian kecil sehingga Miko perlu "
                    f"menggunakan {value_name}."
                ),
                "action": (
                    f"Miko berhenti sejenak, berpikir tenang, lalu "
                    f"mencoba menyelesaikan kejadian kecil itu."
                ),
                "dialogue": '"Hmm... bagaimana ya?"',
                "emotion": "thoughtful",
            },
            {
                "scene_number": 5,
                "duration": raw[4],
                "phase": "HAPPY_ENDING_SIMPLE_LESSON",
                "story": (
                    "Miko berhasil menyelesaikan kejadian kecil "
                    "dan merasa senang."
                ),
                "action": (
                    "Miko tersenyum dan menyampaikan pelajaran "
                    "sederhana dari pengalamannya."
                ),
                "dialogue": '"Yeay! Aku belajar sesuatu hari ini!"',
                "emotion": "joyful",
            },
        ]

        if supporting_name:
            scenes[2]["story"] += (
                f" {supporting_name} ikut berada di dekat Miko."
            )
            scenes[3]["story"] += (
                f" {supporting_name} memberikan dukungan kecil."
            )
            scenes[4]["story"] += (
                f" Miko dan {supporting_name} tersenyum bersama."
            )

        return scenes

    def _build_story(
        self,
        episode_id: str,
        category: str,
        core_value: str,
        location: str,
        supporting_character: Optional[str],
        main_object: Optional[str],
        duration: int,
        language: str,
    ) -> Dict[str, Any]:
        location_data = self._get_location(location)

        supporting_data = (
            self._get_supporting_character(supporting_character)
            if supporting_character
            else None
        )

        object_name = (
            main_object.upper().strip()
            if main_object
            else self._suggest_object(location)
        )

        title = self._generate_title(object_name)
        hook = self._generate_hook(location_data, object_name)
        lesson = self._generate_lesson(core_value)

        scenes = self._build_scenes(
            core_value=core_value,
            location_data=location_data,
            supporting_data=supporting_data,
            main_object=object_name,
            duration=duration,
        )

        voice_script = self._build_voice_script(scenes)

        youtube = self._build_youtube_metadata(
            title=title,
            lesson=lesson,
            category=category,
        )

        return {
            "episode": {
                "id": episode_id,
                "language": language,
                "duration_target": duration,
                "category": category,
                "core_value": core_value,
                "location": location,
                "supporting_characters": (
                    [supporting_character] if supporting_character else []
                ),
                "main_object": object_name,
                "main_character": "MIKO",
            },
            "title": title,
            "hook": hook,
            "lesson": lesson,
            "scenes": scenes,
            "voice_script": voice_script,
            "youtube": youtube,
        }

    @staticmethod
    def _build_voice_script(scenes: List[Dict[str, Any]]) -> str:
        return "\n".join(
            scene["dialogue"].strip()
            for scene in scenes
            if scene.get("dialogue")
        )

    @staticmethod
    def _build_youtube_metadata(
        title: str,
        lesson: str,
        category: str,
    ) -> Dict[str, Any]:
        category_tag = "#" + category.title().replace("_", "")
        return {
            "title": title,
            "description": (
                "Ikuti petualangan Miko dalam cerita singkat "
                "yang seru dan menyenangkan!\n\n"
                f"Pelajaran hari ini: {lesson}\n\n"
                "Cerita untuk anak-anak usia 3-8 tahun."
            ),
            "hashtags": [
                "#Miko",
                "#MikoShorts",
                "#YouTubeShorts",
                "#CeritaAnak",
                "#AnimasiAnak",
                "#BelajarSambilBermain",
                category_tag,
            ],
        }

    def validate_story(self, story: Dict[str, Any]) -> bool:
        if not isinstance(story, dict):
            raise StoryValidationError("Story must be a JSON object.")

        for field in self.story_bible["output_requirements"]["required_fields"]:
            if field not in story:
                raise StoryValidationError(
                    f"Missing required field: {field}"
                )

        episode = story.get("episode", {})

        if episode.get("main_character") != "MIKO":
            raise StoryValidationError(
                "Miko must be the main character."
            )

        scenes = story.get("scenes", [])
        if len(scenes) != 5:
            raise StoryValidationError(
                "Story must contain exactly five scenes."
            )

        total = sum(int(scene.get("duration", 0)) for scene in scenes)
        target = int(episode.get("duration_target", 60))

        if total != target:
            raise StoryValidationError(
                f"Scene duration total ({total}) does not match "
                f"target duration ({target})."
            )

        self._validate_safety(story)
        self._validate_miko_focus(story)
        self._validate_scene_structure(scenes)

        return True

    def _validate_safety(self, story: Dict[str, Any]) -> None:
        # Validate the generated text without importing JSON.
        text_parts: List[str] = []

        def collect(value: Any) -> None:
            if isinstance(value, dict):
                for item in value.values():
                    collect(item)
            elif isinstance(value, list):
                for item in value:
                    collect(item)
            elif isinstance(value, str):
                text_parts.append(value.upper())

        collect(story)
        text = " ".join(text_parts)

        for theme in self.story_bible["safety"]["prohibited_themes"]:
            readable = theme.replace("_", " ").upper()
            if readable in text:
                raise StoryValidationError(
                    f"Potential prohibited theme detected: {theme}"
                )

    @staticmethod
    def _validate_miko_focus(story: Dict[str, Any]) -> None:
        for index, scene in enumerate(story.get("scenes", []), start=1):
            combined = " ".join(
                str(scene.get(key, ""))
                for key in ("story", "action", "dialogue")
            ).lower()

            if "miko" not in combined:
                raise StoryValidationError(
                    f"Scene {index} does not contain Miko."
                )

    def _validate_scene_structure(
        self,
        scenes: List[Dict[str, Any]],
    ) -> None:
        required = self.story_bible["output_requirements"][
            "scene_required_fields"
        ]

        for index, scene in enumerate(scenes, start=1):
            for field in required:
                if field not in scene:
                    raise StoryValidationError(
                        f"Scene {index} missing field: {field}"
                    )

            if int(scene["duration"]) <= 0:
                raise StoryValidationError(
                    f"Scene {index} has invalid duration."
                )


def generate_story(
    category: Optional[str] = None,
    core_value: Optional[str] = None,
    location: Optional[str] = None,
    supporting_character: Optional[str] = None,
    main_object: Optional[str] = None,
    duration: Optional[int] = None,
    language: str = "id",
    episode_id: Optional[str] = None,
) -> Dict[str, Any]:
    return StoryEngine().generate_story(
        category=category,
        core_value=core_value,
        location=location,
        supporting_character=supporting_character,
        main_object=main_object,
        duration=duration,
        language=language,
        episode_id=episode_id,
    )
