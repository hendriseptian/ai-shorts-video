# Miko AI Shorts — Frontend V1

Frontend dashboard for the Cloudflare Python Worker Story Engine V3.

## Files

- `index.html` — dashboard UI
- `style.css` — responsive dark UI
- `script.js` — API connection and Story Engine integration

## API expected

The frontend expects these endpoints:

- `GET /health`
- `GET /story/options`
- `POST /story/generate`

The current Cloudflare Worker V3 already provides these endpoints and CORS.

## Connect the frontend

1. Open the dashboard.
2. Click the ⚙ button.
3. Enter the deployed Worker URL, for example:

```text
https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev
```

4. Click **Save Settings**.
5. The dashboard will load Story Engine options automatically.

The Worker URL is stored in browser `localStorage`, so it does not need to be entered every time on the same browser.

## Generate a story

Select:

- Category
- Core Value
- Location
- Supporting Character
- Language
- Duration
- Optional Main Object
- Optional Episode ID

Then click **GENERATE STORY**.

The result shows:

- Story title
- Hook
- Lesson
- 5 scenes
- Scene duration
- Scene phase
- Emotion
- Dialogue
- Voice script
- YouTube title
- YouTube description
- Hashtags

## Deployment

This frontend is intentionally static and can be hosted separately from the Worker, including GitHub Pages or another static host.

Do not put API secrets in this frontend. Only the public Worker URL belongs here.


## V1.3 behavior

The dropdown catalogue is embedded in the frontend as a safe fallback matching the Miko Story Bible. The UI therefore populates even when `index.html` is opened directly with `file://`.

When the Worker API is reachable, `/story/options` is still requested and its response is used to refresh the dropdowns.

