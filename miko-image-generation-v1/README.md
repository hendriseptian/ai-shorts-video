# Miko AI Shorts — Image Generation V1

This stage adds real image generation using Cloudflare Workers AI.

## Provider

Model:
`@cf/black-forest-labs/flux-1-schnell`

Cloudflare documents this model as a text-to-image model. The Worker AI binding is configured as `AI`, and the generated image is returned as base64. The frontend displays it immediately as a data URI.

## Files

- `src/main.py` — adds `POST /images/generate`
- `src/engines/image_generation_engine.py` — provider engine
- `wrangler.jsonc` — adds the Workers AI binding
- `script.js` — adds Generate Image / Generate All Images UI
- `generated-image-css-addition.css` — optional CSS addition

## Deployment

Replace the corresponding files in your repository, then deploy:

`uv run pywrangler deploy`

After deployment check:

`/health`

It should contain:

- `image_generation_engine: "ready"`
- `image_provider: "cloudflare-workers-ai"`
- `image_model: "@cf/black-forest-labs/flux-1-schnell"`

Then generate a story on GitHub Pages. The Visual Prompts panel should contain:

- Copy Prompt
- Generate Image
- ✨ Generate All Images
- Download

The first generated image is returned directly to the browser. Persistent image storage is intentionally not added yet; that will be a later storage stage.

## Important

Workers AI currently has a free daily allocation of 10,000 neurons. Image generation consumes neurons, so test with one scene first before using Generate All Images.
