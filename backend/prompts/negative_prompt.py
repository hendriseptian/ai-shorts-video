"""
Central negative prompt rules for Miko.

Keep these rules provider-neutral. Provider-specific formatting belongs in
provider adapters, not in the story/scene engine.
"""

BASE_NEGATIVE_PROMPT = (
    "violence, fighting, weapons, blood, injury, horror, gore, frightening scene, "
    "scary monster, dark horror lighting, dangerous imitation, dangerous challenge, "
    "adult themes, sexual content, politics, religious debate, hate, discrimination, "
    "inappropriate language, profanity, disturbing imagery, death as a central theme, "
    "cruelty to animals, dangerous prank, realistic human child, human hair on Miko, "
    "shoes on Miko, clothing other than the blue hoodie, inconsistent character design"
)


def build_negative_prompt(extra: list[str] | None = None) -> str:
    parts = [BASE_NEGATIVE_PROMPT]

    for item in extra or []:
        clean = str(item).strip()
        if clean and clean.lower() not in BASE_NEGATIVE_PROMPT.lower():
            parts.append(clean)

    return ", ".join(parts)
