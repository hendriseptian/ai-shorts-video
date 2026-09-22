from pathlib import Path

source = Path("/mnt/data/Pasted text(20260922-071552).txt").read_text(encoding="utf-8")

# The uploaded text is a line-numbered paste of the current Story Engine.
# Build a clean, copy-pasteable version from the supplied source while applying
# the Cloudflare-friendly resource-loading change.
code = '''from __future__ import annotations

import json
import random
from importlib import resources
from typing import Any, Dict, List, Optional


class StoryEngineError(Exception):
    """Base exception for Story Engine."""


class BibleLoadError(StoryEngineError):
    """Raised when a Bible cannot be loaded."""


class StoryValidationError(StoryEngineError):
    """Raised when generated story fails validation."""


class BibleLoader:
    """Loads the three project Bible files from the packaged engines/config data."""

    CONFIG_PACKAGE = "engines.config"

    CHARACTER_FILE = "character_bible.json"
    STORY_FILE = "story_bible.json"
    WORLD_FILE = "world_bible.json"

    def _load_json(self, filename: str) -> Dict[str, Any]:
        try:
            resource = resources.files(self.CONFIG_PACKAGE).joinpath(filename)

            if not resource.is_file():
                raise BibleLoadError(
                    f"Bible file not found in package "
                    f"{self.CONFIG_PACKAGE}: {filename}"
                )

            data = json.loads(resource.read_text(encoding="utf-8"))

        except BibleLoadError:
            raise
        except Exception as exc:
            raise BibleLoadError(
                f"Unable to load Bible file: {filename}"
            ) from exc

        if not isinstance(data, dict):
            raise BibleLoadError(
                f"Bible must contain a JSON object: {filename}"
            )

        return data

    def load_all(self) -> Dict[str, Dict[str, Any]]:
        return {
            "character": self._load_json(self.CHARACTER_FILE),
            "story": self._load_json(self.STORY_FILE),
            "world": self._load_json(self.WORLD_FILE),
        }


class StoryEngine:
    """
    Main Story Engine.

    V1 creates a structured story using deterministic story-building
    logic. The architecture is provider-independent so an AI provider
    can be connected later without changing the Bible system.
    """

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

        duration = duration or self._get_default_duration()
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
        categories = self.story_bible.get("categories", [])

        if not categories:
            raise StoryEngineError("No story categories found in Story Bible.")

        if category:
            category = category.upper()

            if category not in categories:
                raise StoryEngineError(
                    f"Unknown story category: {category}"
                )

            return category

        return random.choice(categories)

    def _select_core_value(self, core_value: Optional[str]) -> str:
        values = self.story_bible.get("core_values", [])

        if not values:
            raise StoryEngineError("No core values found in Story Bible.")

        if core_value:
            core_value = core_value.upper()

            if core_value not in values:
                raise StoryEngineError(
                    f"Unknown core value: {core_value}"
                )

            return core_value

        return random.choice(values)

    def _select_location(self, location: Optional[str]) -> str:
        locations = self.world_bible.get("locations", [])

        if not locations:
            raise StoryEngineError("No locations found in World Bible.")

        location_map = {
            item["id"]: item
            for item in locations
            if "id" in item
        }

        if location:
            location = location.upper()

            if location not in location_map:
                raise StoryEngineError(
                    f"Unknown location: {location}"
                )

            return location

        weighted_locations = []

        for item in locations:
            location_id = item.get("id")

            if not location_id:
                continue

            if item.get("frequency") == "most_frequently_used":
                weighted_locations.extend([location_id] * 3)
            else:
                weighted_locations.append(location_id)

        if not weighted_locations:
            raise StoryEngineError(
                "No valid locations found in World Bible."
            )

        return random.choice(weighted_locations)

    def _select_supporting_character(
        self,
        supporting_character: Optional[str],
    ) -> Optional[str]:

        characters = self.world_bible.get(
            "supporting_characters",
            [],
        )

        if not characters:
            return None

        character_map = {
            item["id"]: item
            for item in characters
            if "id" in item
        }

        if supporting_character:
            supporting_character = supporting_character.upper()

            if supporting_character not in character_map:
                raise StoryEngineError(
                    f"Unknown supporting character: "
                    f"{supporting_character}"
                )

            return supporting_character

        # 25% chance of a Miko-only episode.
        if random.random() < 0.25:
            return None

        return random.choice(list(character_map.keys()))

    def _get_default_duration(self) -> int:
        return int(
            self.story_bible
            .get("story_identity", {})
            .get("default_duration_seconds", 60)
        )

    def _generate_episode_id(self) -> str:
        return f"MIKO-{random.randint(1, 999999):06d}"

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

        supporting_data = None

        if supporting_character:
            supporting_data = self._get_supporting_character(
                supporting_character
            )

        object_name = (
            main_object.upper()
            if main_object
            else self._suggest_object(category, location)
        )

        title = self._generate_title(
            category=category,
            location=location_data,
            main_object=object_name,
        )

        hook = self._generate_hook(
            location=location_data,
            main_object=object_name,
        )

        lesson = self._generate_lesson(core_value)

        scenes = self._build_scenes(
            category=category,
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
            core_value=core_value,
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
                    [supporting_character]
                    if supporting_character
                    else []
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

    def _get_location(self, location_id: str) -> Dict[str, Any]:
        for location in self.world_bible.get("locations", []):
            if location.get("id") == location_id:
                return location

        raise StoryEngineError(
            f"Location not found: {location_id}"
        )

    def _get_supporting_character(
        self,
        character_id: str,
    ) -> Dict[str, Any]:

        # Supporting characters are defined in the World Bible in V1.
        for character in self.world_bible.get(
            "supporting_characters",
            [],
        ):
            if character.get("id") == character_id:
                return character

        # Fallback to Character Bible if a future Bible version moves
        # supporting characters there.
        for character in self.character_bible.get(
            "supporting_characters",
            [],
        ):
            if character.get("id") == character_id:
                return character

        raise StoryEngineError(
            f"Supporting character not found: {character_id}"
        )

    def _suggest_object(
        self,
        category: str,
        location: str,
    ) -> str:

        location_objects = {
            "MIKOS_HOUSE": [
                "STORY_BOOK",
                "CRAYONS",
                "TEDDY_BEAR",
                "BALLOON",
            ],
            "RAINBOW_PARK": [
                "RAINBOW",
                "BALL",
                "SOAP_BUBBLES",
                "BUTTERFLY",
            ],
            "SUNNY_FOREST": [
                "RAINBOW",
                "LITTLE_STREAM",
                "MUSHROOM",
                "FEATHER",
                "BUTTERFLY",
            ],
            "SUNNY_BEACH": [
                "SEASHELL",
                "BEACH_BALL",
                "SMALL_BOAT",
                "COLORFUL_UMBRELLA",
            ],
            "LITTLE_SCHOOL": [
                "CRAYONS",
                "SHAPE_BLOCKS",
                "STORY_BOOK",
                "COLOR_CARDS",
            ],
            "PLAYGROUND": [
                "BALL",
                "SOAP_BUBBLES",
                "BALLOON",
            ],
            "FLOWER_GARDEN": [
                "SUNFLOWER",
                "WATERING_CAN",
                "BUTTERFLY",
                "LITTLE_BEE",
            ],
            "LITTLE_FARM": [
                "CARROT",
                "WATERING_CAN",
                "BASKET",
                "FEATHER",
            ],
            "CLOUD_HILL": [
                "ANIMAL_SHAPED_CLOUD",
                "RAINBOW",
                "FALLING_STAR",
            ],
            "MIKOS_NIGHT_GARDEN": [
                "FIREFLY",
                "GLOWING_FLOWER",
                "STAR",
                "MOON",
            ],
        }

        objects = location_objects.get(
            location,
            ["COLORFUL_TOY"],
        )

        return random.choice(objects)

    def _generate_title(
        self,
        category: str,
        location: Dict[str, Any],
        main_object: str,
    ) -> str:

        object_name = main_object.replace(
            "_",
            " ",
        ).title()

        templates = [
            f"Miko Menemukan {object_name}!",
            f"Miko dan {object_name}",
            f"Petualangan Miko: {object_name}",
            f"Miko Penasaran dengan {object_name}",
        ]

        return random.choice(templates)

    def _generate_hook(
        self,
        location: Dict[str, Any],
        main_object: str,
    ) -> str:

        location_name = location.get(
            "name",
            "tempat baru",
        )

        object_name = main_object.replace(
            "_",
            " ",
        ).lower()

        return (
            f"Miko melihat sesuatu yang menarik di "
            f"{location_name.lower()}: {object_name}!"
        )

    def _generate_lesson(
        self,
        core_value: str,
    ) -> str:

        lessons = {
            "KINDNESS":
                "Berbuat baik kepada orang lain membuat suasana menjadi lebih bahagia.",
            "SHARING":
                "Berbagi membuat bermain dan belajar menjadi lebih menyenangkan.",
            "HONESTY":
                "Berkata jujur membantu kita menyelesaikan masalah dengan baik.",
            "COURAGE":
                "Berani mencoba membantu kita menemukan hal baru.",
            "PATIENCE":
                "Bersabar membantu kita menyelesaikan sesuatu dengan lebih baik.",
            "CURIOSITY":
                "Rasa ingin tahu membantu kita belajar menemukan hal baru.",
            "HELPING_OTHERS":
                "Membantu orang lain adalah hal baik yang membuat kita merasa bahagia.",
            "RESPECT":
                "Menghargai orang lain membuat kita bisa bermain dan belajar bersama.",
            "CLEANLINESS":
                "Menjaga kebersihan membuat lingkungan menjadi nyaman.",
            "TEAMWORK":
                "Bekerja bersama membuat masalah terasa lebih mudah.",
            "PROBLEM_SOLVING":
                "Berpikir tenang membantu kita menemukan solusi.",
            "LEARNING_FROM_MISTAKES":
                "Kesalahan bisa menjadi kesempatan untuk belajar.",
            "RESPONSIBILITY":
                "Merawat sesuatu dengan baik adalah bentuk tanggung jawab.",
            "EMPATHY":
                "Memahami perasaan orang lain membantu kita menjadi teman yang baik.",
            "GRATITUDE":
                "Menghargai hal-hal kecil membuat kita merasa lebih bahagia.",
            "SELF_CONFIDENCE":
                "Percaya pada diri sendiri membantu kita berani mencoba.",
            "TAKING_CARE_OF_NATURE":
                "Menjaga alam membantu lingkungan tetap indah dan nyaman.",
        }

        return lessons.get(
            core_value,
            "Setiap pengalaman bisa menjadi kesempatan untuk belajar.",
        )

    def _build_scenes(
        self,
        category: str,
        core_value: str,
        location_data: Dict[str, Any],
        supporting_data: Optional[Dict[str, Any]],
        main_object: str,
        duration: int,
    ) -> List[Dict[str, Any]]:

        standard_durations = [5, 10, 20, 15, 10]

        if duration <= 0:
            raise StoryEngineError(
                "Duration must be greater than zero."
            )

        scale = duration / 60

        scene_durations = [
            max(1, round(value * scale))
            for value in standard_durations
        ]

        difference = duration - sum(scene_durations)
        scene_durations[-1] += difference

        if scene_durations[-1] <= 0:
            raise StoryEngineError(
                "Duration is too short for the five-scene structure."
            )

        supporting_name = (
            supporting_data.get("name")
            if supporting_data
            else None
        )

        object_name = main_object.replace(
            "_",
            " ",
        ).lower()

        location_name = location_data.get(
            "name",
            "tempat",
        )

        scenes = [
            {
                "scene_number": 1,
                "duration": scene_durations[0],
                "phase": "MIKO_SEES",
                "story": (
                    f"Miko berada di {location_name.lower()} "
                    f"ketika melihat {object_name}."
                ),
                "action": (
                    f"Miko berhenti bermain dan memperhatikan "
                    f"{object_name} dengan rasa ingin tahu."
                ),
                "dialogue": '"Wah, itu apa ya?"',
                "emotion": "curious",
            },
            {
                "scene_number": 2,
                "duration": scene_durations[1],
                "phase": "MIKO_DISCOVERS",
                "story": (
                    f"Miko mendekati {object_name} untuk melihatnya "
                    f"lebih dekat."
                ),
                "action": (
                    f"Miko berjalan mendekat, melihat dari berbagai "
                    f"sisi, lalu menemukan sesuatu yang menarik."
                ),
                "dialogue": f'"Ohh... ternyata {object_name}!"',
                "emotion": "excited",
            },
            {
                "scene_number": 3,
                "duration": scene_durations[2],
                "phase": "MIKO_PLAYS_TRIES_EXPLORES",
                "story": (
                    f"Miko mencoba berinteraksi dengan "
                    f"{object_name} dengan cara yang aman."
                ),
                "action": (
                    f"Miko mencoba, bermain atau mengeksplorasi "
                    f"{object_name} sambil menunjukkan rasa penasaran."
                ),
                "dialogue": '"Aku coba!"',
                "emotion": "playful",
            },
            {
                "scene_number": 4,
                "duration": scene_durations[3],
                "phase": "SOMETHING_HAPPENS",
                "story": (
                    "Terjadi kejadian kecil yang membuat Miko "
                    "harus berpikir dan bertindak."
                ),
                "action": (
                    f"Miko menghadapi kejutan kecil yang sesuai "
                    f"dengan tema {core_value.lower().replace('_', ' ')}."
                ),
                "dialogue": '"Hmm... bagaimana ya?"',
                "emotion": "slightly_worried",
            },
            {
                "scene_number": 5,
                "duration": scene_durations[4],
                "phase": "HAPPY_ENDING_SIMPLE_LESSON",
                "story": (
                    "Miko berhasil menyelesaikan kejadian kecil "
                    "dan merasa senang."
                ),
                "action": (
                    f"Miko tersenyum dan menikmati akhir yang "
                    f"bahagia bersama {supporting_name or 'pengalaman barunya'}."
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

    def _build_voice_script(
        self,
        scenes: List[Dict[str, Any]],
    ) -> str:

        dialogue_lines = []

        for scene in scenes:
            dialogue = scene.get("dialogue")

            if dialogue:
                dialogue_lines.append(
                    dialogue.strip()
                )

        return "\n".join(dialogue_lines)

    def _build_youtube_metadata(
        self,
        title: str,
        lesson: str,
        category: str,
        core_value: str,
    ) -> Dict[str, Any]:

        hashtags = [
            "#Miko",
            "#MikoShorts",
            "#YouTubeShorts",
            "#CeritaAnak",
            "#AnimasiAnak",
            "#BelajarSambilBermain",
            f"#{category.title().replace('_', '')}",
        ]

        return {
            "title": title,
            "description": (
                f"Ikuti petualangan Miko dalam cerita singkat yang "
                f"seru dan menyenangkan!\n\n"
                f"Pelajaran hari ini: {lesson}\n\n"
                f"Cerita untuk anak-anak usia 3-8 tahun."
            ),
            "hashtags": hashtags,
        }

    def validate_story(
        self,
        story: Dict[str, Any],
    ) -> bool:

        if not isinstance(story, dict):
            raise StoryValidationError(
                "Story must be a JSON object."
            )

        required_fields = (
            self.story_bible
            .get("output_requirements", {})
            .get("required_fields", [])
        )

        for field in required_fields:
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

        if not scenes:
            raise StoryValidationError(
                "Story must contain scenes."
            )

        scene_total = sum(
            int(scene.get("duration", 0))
            for scene in scenes
        )

        target_duration = int(
            episode.get("duration_target", 60)
        )

        if scene_total != target_duration:
            raise StoryValidationError(
                f"Scene duration total ({scene_total}) does not match "
                f"target duration ({target_duration})."
            )

        self._validate_safety(story)
        self._validate_miko_focus(story)
        self._validate_scene_structure(scenes)

        return True

    def _validate_safety(
        self,
        story: Dict[str, Any],
    ) -> None:

        prohibited = set(
            self.story_bible
            .get("safety", {})
            .get("prohibited_themes", [])
        )

        text = json.dumps(
            story,
            ensure_ascii=False,
        ).upper()

        for theme in prohibited:
            readable_theme = theme.replace(
                "_",
                " ",
            ).upper()

            if readable_theme in text:
                raise StoryValidationError(
                    f"Potential prohibited theme detected: {theme}"
                )

    def _validate_miko_focus(
        self,
        story: Dict[str, Any],
    ) -> None:

        scenes = story.get("scenes", [])

        if not scenes:
            raise StoryValidationError(
                "No scenes available for focus validation."
            )

        for index, scene in enumerate(
            scenes,
            start=1,
        ):
            combined = " ".join(
                str(scene.get(key, ""))
                for key in [
                    "story",
                    "action",
                    "dialogue",
                ]
            ).lower()

            if "miko" not in combined:
                raise StoryValidationError(
                    f"Scene {index} does not contain Miko."
                )

    def _validate_scene_structure(
        self,
        scenes: List[Dict[str, Any]],
    ) -> None:

        required_fields = (
            self.story_bible
            .get("output_requirements", {})
            .get("scene_required_fields", [])
        )

        for index, scene in enumerate(
            scenes,
            start=1,
        ):
            for field in required_fields:
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

    engine = StoryEngine()

    return engine.generate_story(
        category=category,
        core_value=core_value,
        location=location,
        supporting_character=supporting_character,
        main_object=main_object,
        duration=duration,
        language=language,
        episode_id=episode_id,
    )


if __name__ == "__main__":

    print("=" * 60)
    print("MIKO STORY ENGINE V1")
    print("=" * 60)

    try:
        engine = StoryEngine()

        story = engine.generate_story(
            category="ADVENTURE",
            core_value="COURAGE",
            location="SUNNY_FOREST",
            supporting_character="KIKI",
            main_object="RAINBOW",
            duration=60,
            language="id",
        )

        print(
            json.dumps(
                story,
                ensure_ascii=False,
                indent=2,
            )
        )

        print()
        print("=" * 60)
        print("STORY VALIDATION: PASSED")
        print("=" * 60)

    except StoryEngineError as exc:
        print()
        print("STORY ENGINE ERROR:")
        print(exc)
'''

out = Path("/mnt/data/story_engine_v2.py")
out.write_text(code, encoding="utf-8")

print(f"Created: {out}")
print(f"Lines: {len(code.splitlines())}")
