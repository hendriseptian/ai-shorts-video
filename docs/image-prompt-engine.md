# Image Prompt Engine V1

## Purpose

Convert an existing Miko Story Engine response into one structured visual
prompt per scene.

This version is provider-neutral. It does not call Gemini, Cloudflare, or any
other image generation API.

## Flow

Story Engine
→ Scene list
→ Image Prompt Engine
→ Character Consistency Lock
→ World/Location Lock
→ Negative Prompt
→ Structured Image Prompt

## Output

Each scene returns:

- `prompt`
- `negative_prompt`
- `aspect_ratio`
- `resolution`
- `style`
- `character_lock`
- `world_lock`
- `metadata`

Default visual target:

- 9:16
- 1080x1920
- polished stylized 3D children's animation

## Character lock

Miko remains:

- orange-and-white kitten
- large dark-brown eyes
- fluffy orange fur
- white muzzle/cheeks/chest/belly/paws/tail tip
- bright blue hoodie
- white drawstrings
- round paw pendant
- no shoes

## Important

This stage only prepares prompts. Image generation provider integration comes
after the prompt output is tested and stable.
