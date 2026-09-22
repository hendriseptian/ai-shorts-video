from __future__ import annotations

import base64
import binascii
import json
from typing import Any, Optional

from js import Blob, FormData, Response, Uint8Array


MODEL = "@cf/black-forest-labs/flux-2-klein-4b"
DEFAULT_WIDTH = 576
DEFAULT_HEIGHT = 1024


MIKO_HARD_LOCK = """
SUBJECT IDENTITY IS ABSOLUTE.

Miko is a CUTE 3D ANIMATED MALE KITTEN / CAT.
Miko MUST be visibly and unmistakably a FELINE.
Miko is NOT a human child, NOT a human boy, NOT a person, and NOT a humanoid human.

Miko's permanent visual identity:
- orange-and-white kitten fur
- feline head and face
- triangular cat ears
- feline muzzle and small cat nose
- visible whiskers
- large dark-brown feline eyes
- fluffy orange fur
- white muzzle, cheeks, chest, belly, paws and tail tip
- small kitten body
- short feline legs
- four furry cat paws
- long fluffy feline tail
- bright blue hoodie with white drawstrings
- small round paw pendant
- no shoes
- no human skin
- no human hair

The character must remain a CAT in every scene even when standing, walking,
playing, holding an object, or interacting with other characters.
Do not reinterpret Miko as a human child or humanoid person.
"""


MIKO_NEGATIVE_LOCK = """
human, person, human child, human boy, human girl, human face, human body,
human anatomy, human skin, human hair, human hands, human feet, human arms,
human legs, humanoid human, realistic person, live action human,
human-like face, human-like body, human character,
dog, puppy, fox, wolf, bear, rabbit, squirrel, other animal as Miko,
wrong species, different species, creature without feline features,
missing cat ears, missing whiskers, missing tail,
clothing other than blue hoodie, shoes on Miko,
adult, violence, blood, injury, horror, gore, frightening scene,
weapons, politics, sexual content, profanity, disturbing imagery
"""


class ImageGenerationEngineError(Exception):
    pass


def _decode_data_uri(value: str) -> tuple[bytes, str]:
    if not value or not isinstance(value, str):
        raise ImageGenerationEngineError("Miko reference image is required.")

    raw = value.strip()
    if "," not in raw or not raw.startswith("data:image/"):
        raise ImageGenerationEngineError(
            "Miko reference must be a PNG/JPEG data URL."
        )

    header, payload = raw.split(",", 1)
    mime = header[5:].split(";", 1)[0].lower()

    if mime not in {"image/png", "image/jpeg", "image/webp"}:
        raise ImageGenerationEngineError(
            "Miko reference must be PNG, JPEG, or WebP."
        )

    try:
        return base64.b64decode(payload, validate=True), mime
    except (binascii.Error, ValueError) as exc:
        raise ImageGenerationEngineError(
            "Miko reference image is not valid Base64."
        ) from exc


def _bytes_to_uint8(data: bytes):
    # Pyodide FFI: construct a JavaScript Uint8Array from Python bytes.
    return Uint8Array.new(data)


async def _run_flux2_with_reference(
    ai,
    prompt: str,
    reference_bytes: bytes,
    reference_mime: str,
    width: int,
    height: int,
    seed: Optional[int] = None,
):
    """
    FLUX.2 Klein 4B uses multipart input on Workers AI.
    The reference image is sent as input_image_0.
    """
    blob = Blob.new([_bytes_to_uint8(reference_bytes)], {"type": reference_mime})

    form = FormData.new()
    form.append("prompt", prompt)
    form.append("input_image_0", blob, "miko-reference")
    form.append("width", str(width))
    form.append("height", str(height))
    if seed is not None:
        form.append("seed", str(seed))

    # Cloudflare's documented Workers AI multipart pattern:
    # serialize FormData through a Response, then pass the stream + content type.
    form_response = Response.new(form)
    body = form_response.body
    content_type = form_response.headers.get("content-type")

    result = await ai.run(
        MODEL,
        {
            "multipart": {
                "body": body,
                "contentType": content_type,
            }
        },
    )
    return result


def _extract_image(result: Any) -> Optional[str]:
    if result is None:
        return None

    # Most current FLUX.2 Workers AI responses expose result.image.
    image = getattr(result, "image", None)
    if image:
        return str(image)

    if isinstance(result, dict):
        image = result.get("image")
        if image:
            return image

    return None


class ImageGenerationEngine:
    version = "0.4.0"
    provider = "cloudflare-workers-ai"
    model = MODEL

    def __init__(self, ai=None):
        self.ai = ai

    async def generate(
        self,
        *,
        prompt: str,
        negative_prompt: str = "",
        reference_image: str,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        seed: Optional[int] = None,
        scene_number: Optional[int] = None,
    ) -> dict[str, Any]:
        if self.ai is None:
            raise ImageGenerationEngineError("Workers AI binding is not configured.")

        if not prompt.strip():
            raise ImageGenerationEngineError("Image prompt is empty.")

        if width != 576 or height != 1024:
            # Keep the first consistency test deterministic.
            width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT

        reference_bytes, reference_mime = _decode_data_uri(reference_image)

        full_prompt = f"""
{MIKO_HARD_LOCK}

REFERENCE IMAGE RULE:
The attached reference image is the MASTER VISUAL REFERENCE for Miko.
Use the same kitten identity, species, fur pattern, face, eyes, ears,
muzzle, tail, body proportions, and blue hoodie from the reference.
Preserve Miko as a cat. Do not redesign Miko.

SCENE REQUEST:
{prompt}

VISUAL REQUIREMENTS:
polished stylized 3D children's animation, rounded proportions,
soft fluffy fur, expressive animation, bright warm lighting,
wholesome family-friendly atmosphere, clean cinematic composition,
vertical 9:16 composition, Miko clearly visible and large enough.

Do not add written text, captions, logos, or watermarks.
""".strip()

        full_negative = f"""
{MIKO_NEGATIVE_LOCK}
{negative_prompt}
""".strip()

        # FLUX.2 Klein uses the positive prompt for generation. Keep the
        # negative lock in the prompt itself so the species constraint remains
        # explicit even though the model does not expose a native negative_prompt.
        final_prompt = f"""
{full_prompt}

ABSOLUTE AVOID LIST:
{full_negative}
""".strip()

        result = await _run_flux2_with_reference(
            self.ai,
            final_prompt,
            reference_bytes,
            reference_mime,
            width,
            height,
            seed,
        )

        image = _extract_image(result)
        if not image:
            raise ImageGenerationEngineError(
                "FLUX.2 returned no image. Check the Workers AI response."
            )

        if not image.startswith("data:image/"):
            image = f"data:image/png;base64,{image}"

        return {
            "success": True,
            "scene_number": scene_number,
            "provider": self.provider,
            "model": self.model,
            "width": width,
            "height": height,
            "resolution": f"{width}x{height}",
            "aspect_ratio": "9:16",
            "image": image,
            "character_reference_used": True,
            "character_identity": "MIKO_CAT",
            "character_lock": "STRICT",
            "negative_prompt": full_negative,
        }
