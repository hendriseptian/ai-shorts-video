"""
World/location visual locks for Miko.

The current Story Engine supplies a location id/name. These descriptions keep
the visual identity of recurring locations stable across scenes.
"""

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


def get_world_lock(location: str | None) -> str:
    value = str(location or "").strip()

    if value in WORLD_LOCKS:
        return WORLD_LOCKS[value]

    normalized = value.upper().replace(" ", "_").replace("'", "")

    if normalized in WORLD_LOCKS:
        return WORLD_LOCKS[normalized]

    return (
        "bright, warm, cheerful and safe Miko world, detailed but non-distracting "
        "background, family-friendly atmosphere"
    )
