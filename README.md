# AI Shorts Video

AI-powered YouTube Shorts production system.

This project is designed to automate the production of short-form
children's videos using AI, from story generation to video production,
voice generation, editing, quality control, and YouTube publishing.

## Project Goal

The system will eventually support:

- Story generation
- Scene generation
- AI image/video generation
- Character consistency
- AI voice generation
- Automatic video editing
- Quality control
- YouTube metadata generation
- YouTube upload
- Scheduled publishing
- Production dashboard
- Episode history and tracking

## Main Character

The main character of this project is:

**Miko**

Miko is a cute orange-and-white 3D animated kitten designed for
children's YouTube Shorts.

Character consistency is a core requirement of this project.

## Production Pipeline

```text
STORY
  ↓
SCENE
  ↓
VIDEO
  ↓
VOICE
  ↓
EDIT
  ↓
QC
  ↓
YOUTUBE
  ↓
PUBLISH
```

Each stage will be implemented as an independent engine.

## Planned Engines

### 1. Story Engine

Generates a complete Miko story based on:

- Story category
- Core value
- Location
- Supporting character
- Main object
- Target duration
- Language

### 2. Scene Engine

Converts the story into production-ready scenes.

Each scene contains:

- Character
- Location
- Props
- Action
- Emotion
- Camera
- Lighting
- Visual prompt
- Video direction
- Negative prompt
- Continuity information

### 3. Video Engine

Generates video clips from scene specifications.

The engine will support:

- Multiple AI video providers
- Provider fallback
- Retry system
- Character reference images
- Vertical 9:16 video
- Video quality control

### 4. Voice Engine

Generates Miko's voice and other required dialogue.

Voice requirements:

- Childlike boy voice
- Approximately 5–7 years old impression
- Warm
- Cheerful
- Innocent
- Energetic
- Clear Indonesian pronunciation

### 5. Edit Engine

Combines:

- Video clips
- Voice
- Background music
- Sound effects
- Transitions
- Subtitles

Final target:

```text
1080 x 1920
9:16
YouTube Shorts
```

### 6. QC Engine

Checks generated content before publishing.

Examples:

- Video exists
- Correct duration
- Correct aspect ratio
- Miko consistency
- No obvious character mutation
- No extra limbs
- No disturbing imagery
- No unwanted text
- No watermark
- Audio exists
- Story matches generated scenes

### 7. YouTube Engine

Handles:

- Title
- Description
- Hashtags
- Upload
- Thumbnail
- Scheduling
- Publishing status

### 8. Automation Engine

Eventually controls the complete production process.

Example:

```text
Every day
   ↓
Generate story
   ↓
Generate scenes
   ↓
Generate video
   ↓
Generate voice
   ↓
Edit
   ↓
QC
   ↓
Upload to YouTube
```

## Project Structure

```text
ai-shorts-video/
│
├── README.md
├── .gitignore
├── .env.example
├── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── backend/
│   ├── main.py
│   │
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── story_engine.py
│   │   ├── scene_engine.py
│   │   ├── video_engine.py
│   │   ├── voice_engine.py
│   │   ├── edit_engine.py
│   │   ├── qc_engine.py
│   │   ├── youtube_engine.py
│   │   └── automation_engine.py
│   │
│   ├── prompts/
│   │   ├── story_prompt.py
│   │   ├── scene_prompt.py
│   │   └── video_prompt.py
│   │
│   ├── models/
│   │   ├── character.py
│   │   ├── story.py
│   │   ├── scene.py
│   │   └── episode.py
│   │
│   └── config/
│       ├── character_bible.json
│       ├── story_bible.json
│       └── world_bible.json
│
├── assets/
│   └── miko/
│       ├── reference/
│       └── props/
│
├── data/
│   ├── episodes/
│   └── history/
│
├── generated/
│   └── .gitkeep
│
├── scripts/
│   ├── generate_episode.py
│   └── test_pipeline.py
│
└── docs/
    ├── architecture.md
    ├── character.md
    ├── story-engine.md
    ├── scene-engine.md
    └── video-engine.md
```

## Development Philosophy

The project is designed as a modular AI production pipeline.

Each engine should have a clear responsibility and should be replaceable
without breaking the rest of the system.

```text
Story Engine
     ↓
Story JSON
     ↓
Scene Engine
     ↓
Scene JSON
     ↓
Video Engine
     ↓
Video Clips
```

AI providers should be abstracted so that the provider can be changed
without rewriting the entire application.

## Configuration

Environment variables will be stored locally in:

```text
.env
```

The `.env` file must never be committed to GitHub.

Use:

```text
.env.example
```

as the configuration template.

## Media Storage

Large generated files such as MP4, MP3, WAV, PNG, JPG and similar
media should not normally be stored in Git history.

Generated media should eventually use external/object storage.

GitHub should primarily contain:

- Source code
- Configuration
- Prompts
- Character Bible
- Story Bible
- World Bible
- Documentation
- Metadata

## Current Development Stage

### V0.1 — Foundation

Current focus:

- Repository structure
- Character Bible
- Story Bible
- World Bible
- Basic project configuration

### V0.2 — Story Engine

Planned:

- Story generation
- JSON output
- Safety validation
- Story history
- Repetition prevention

### V0.3 — Scene Engine

Planned:

- Scene generation
- Visual prompts
- Camera direction
- Continuity

### V0.4 — Video Engine

Planned:

- AI video providers
- Provider abstraction
- Retry system
- Reference image support

### V0.5 — Voice Engine

Planned:

- Miko voice
- Dialogue generation
- Audio generation

### V0.6 — Edit Engine

Planned:

- FFmpeg
- Video assembly
- Voice synchronization
- Music
- Sound effects
- Subtitles

### V0.7 — QC Engine

Planned:

- Automated checks
- Character consistency
- Video validation
- Audio validation

### V0.8 — YouTube Engine

Planned:

- Metadata
- Upload
- Scheduling
- Publishing

### V1.0 — Full Automation

Target:

```text
IDEA
 ↓
STORY
 ↓
SCENES
 ↓
VIDEO
 ↓
VOICE
 ↓
EDIT
 ↓
QC
 ↓
YOUTUBE
 ↓
PUBLISHED
```

## License

This project is currently private/personal and is not intended for
redistribution without permission.
