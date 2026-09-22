"""
Miko Story Engine Bible data.

Cloudflare Python Workers version:
- No filesystem access
- No JSON/resource loading
- All immutable Bible/config data is embedded as Python dictionaries
"""

CHARACTER_BIBLE = {
    "main_character": {
        "id": "MIKO",
        "name": "Miko",
        "species": "kitten",
        "gender": "male",
        "age_impression": "4-6",
        "appearance": {
            "fur": "orange and white",
            "eyes": "large round expressive dark-brown eyes",
            "clothes": "bright blue hoodie with white drawstrings and paw-shaped pendant",
            "shoes": "none",
            "paw_pads": "soft pink",
        },
        "personality": [
            "curious", "cheerful", "kind-hearted", "brave",
            "playful", "friendly", "slightly clumsy", "helpful",
        ],
        "voice": {
            "type": "cute childlike boy",
            "age_impression": "5-7",
            "language": "Indonesian",
            "style": "warm cheerful innocent energetic expressive",
        },
        "target_audience": "children 3-8",
    },
    "supporting_characters": [
        {
            "id": "LULU",
            "name": "Lulu",
            "species": "rabbit",
            "personality": "cheerful, friendly, energetic",
        },
        {
            "id": "BOBI",
            "name": "Bobi",
            "species": "small bear",
            "personality": "gentle, slightly shy, kind",
        },
        {
            "id": "KIKI",
            "name": "Kiki",
            "species": "small bird",
            "personality": "energetic, curious, quick to discover",
        },
        {
            "id": "TOTO",
            "name": "Toto",
            "species": "turtle",
            "personality": "calm, patient, thoughtful",
        },
        {
            "id": "NANA",
            "name": "Nana",
            "species": "squirrel",
            "personality": "playful, energetic, slightly clumsy",
        },
    ],
}

WORLD_BIBLE = {
    "locations": [
        {
            "id": "MIKOS_HOUSE",
            "name": "Miko's House",
            "frequency": "regular",
            "description": "small cozy house with cream walls, blue door, round windows, red-orange roof and small yard",
        },
        {
            "id": "RAINBOW_PARK",
            "name": "Rainbow Park",
            "frequency": "most_frequently_used",
            "description": "green grass, big tree, colorful flowers, bench, path, swing, slide, small pond, butterflies and birds",
        },
        {
            "id": "SUNNY_FOREST",
            "name": "Sunny Forest",
            "frequency": "regular",
            "description": "safe bright forest with trees, mushrooms, flowers, bushes, rocks, small stream, birds, rabbits and butterflies",
        },
        {
            "id": "SUNNY_BEACH",
            "name": "Sunny Beach",
            "frequency": "regular",
            "description": "bright sandy beach with blue sea, shells, rocks, umbrella, bucket, beach ball and small boat",
        },
        {
            "id": "LITTLE_SCHOOL",
            "name": "Little School",
            "frequency": "regular",
            "description": "friendly classroom with board, small desks, chairs, bookshelf, schoolyard and small garden",
        },
        {
            "id": "PLAYGROUND",
            "name": "Playground",
            "frequency": "regular",
            "description": "safe playground with slide, swing, sandbox, balls and jungle gym",
        },
        {
            "id": "FLOWER_GARDEN",
            "name": "Flower Garden",
            "frequency": "regular",
            "description": "bright garden with sunflowers, tulips, daisies, lavender, butterflies and friendly bees",
        },
        {
            "id": "LITTLE_FARM",
            "name": "Little Farm",
            "frequency": "regular",
            "description": "small safe farm with chicken coop, cows, goats, rabbits, vegetable garden and barn",
        },
        {
            "id": "CLOUD_HILL",
            "name": "Cloud Hill",
            "frequency": "regular",
            "description": "imaginative sunny hill with sky views and soft animal-shaped clouds",
        },
        {
            "id": "MIKOS_NIGHT_GARDEN",
            "name": "Miko's Night Garden",
            "frequency": "regular",
            "description": "calm cozy night garden with moon, stars, glowing flowers and fireflies",
        },
    ],
    "supporting_characters": CHARACTER_BIBLE["supporting_characters"],
}

STORY_BIBLE = {
    "story_identity": {
        "default_duration_seconds": 60,
        "target_audience": "children 3-8",
        "main_character": "MIKO",
        "story_formula": [
            "MIKO_SEES",
            "MIKO_DISCOVERS",
            "MIKO_PLAYS_TRIES_EXPLORES",
            "SOMETHING_HAPPENS",
            "HAPPY_ENDING_SIMPLE_LESSON",
        ],
    },
    "categories": [
        "ADVENTURE",
        "FUNNY",
        "FRIENDSHIP",
        "DISCOVERY",
        "LEARNING",
        "HELPING_OTHERS",
        "ANIMAL_FRIENDS",
        "NATURE",
        "SIMPLE_PROBLEM_SOLVING",
        "EVERYDAY_LIFE",
        "IMAGINATION",
        "MUSIC_AND_PLAY",
    ],
    "core_values": [
        "KINDNESS",
        "SHARING",
        "HONESTY",
        "COURAGE",
        "PATIENCE",
        "CURIOSITY",
        "HELPING_OTHERS",
        "RESPECT",
        "CLEANLINESS",
        "TEAMWORK",
        "PROBLEM_SOLVING",
        "LEARNING_FROM_MISTAKES",
        "RESPONSIBILITY",
        "EMPATHY",
        "GRATITUDE",
        "SELF_CONFIDENCE",
        "TAKING_CARE_OF_NATURE",
    ],
    "safety": {
        "prohibited_themes": [
            "VIOLENCE",
            "FIGHTING",
            "WEAPONS",
            "BLOOD",
            "INJURY",
            "HORROR",
            "GORE",
            "FRIGHTENING_SCENES",
            "MONSTERS_THAT_ARE_DESIGNED_TO_SCARE",
            "DANGEROUS_IMITATION",
            "DANGEROUS_CHALLENGES",
            "ADULT_THEMES",
            "SEXUAL_CONTENT",
            "POLITICS",
            "RELIGIOUS_DEBATES",
            "HATE",
            "DISCRIMINATION",
            "INAPPROPRIATE_LANGUAGE",
            "PROFANITY",
            "DISTURBING_IMAGERY",
            "DEATH_AS_A_CENTRAL_THEME",
            "CRUELTY_TO_ANIMALS",
            "DANGEROUS_PRANKS",
        ]
    },
    "output_requirements": {
        "required_fields": [
            "episode",
            "title",
            "hook",
            "lesson",
            "scenes",
            "voice_script",
            "youtube",
        ],
        "scene_required_fields": [
            "scene_number",
            "duration",
            "phase",
            "story",
            "action",
            "dialogue",
            "emotion",
        ],
    },
}
