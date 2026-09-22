"""
Local smoke test for Image Prompt Engine V1.

Run from the backend directory:
    python ../scripts/test_image_prompt.py

Or from the project root if PYTHONPATH includes backend.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from engines.image_prompt_engine import ImagePromptEngine


SAMPLE_STORY = {
    "episode": {
        "episode_id": "MIKO-0001",
        "language": "id",
        "location": "MIKOS_HOUSE",
    },
    "title": "Miko dan Teddy Bear",
    "scenes": [
        {
            "scene_number": 1,
            "phase": "MIKO_SEES",
            "story": "Miko melihat teddy bear di Miko's House.",
            "emotion": "curious",
            "dialogue": "Wah, itu apa ya?",
        },
        {
            "scene_number": 2,
            "phase": "MIKO_DISCOVERS",
            "story": "Miko mendekati teddy bear untuk melihatnya lebih dekat.",
            "emotion": "excited",
            "dialogue": "Ohh... ternyata teddy bear!",
        },
    ],
}


def main() -> None:
    result = ImagePromptEngine().generate_for_story(SAMPLE_STORY)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    assert result["success"] is True
    assert result["scene_count"] == 2
    assert len(result["prompts"]) == 2

    first = result["prompts"][0]

    assert "orange-and-white kitten" in first["prompt"]
    assert "bright blue hoodie" in first["prompt"]
    assert first["aspect_ratio"] == "9:16"
    assert first["resolution"] == "1080x1920"
    assert first["negative_prompt"]

    print("\nIMAGE PROMPT ENGINE V1: PASS")


if __name__ == "__main__":
    main()
