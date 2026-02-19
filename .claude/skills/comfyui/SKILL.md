---
name: comfyui
description: Generate images using ComfyUI Z-Image Turbo 6B (~6s/image). 21 profiles, 20 styles, 15 filters, AVIF/WebP/JPEG with full controls.
argument-hint: [prompt] [--profile hero-home] [--style cinematic] [--filter warm] [--seed NUMBER]
allowed-tools: Bash(python3 .claude/skills/comfyui/generate.py *), Read
context: fork
---
# ComfyUI Image Generation

Generate images by running a single command. Do NOT explore, discover models, construct payloads, or deviate.

## Usage

```bash
python3 .claude/skills/comfyui/generate.py --prompt "PROMPT" [OPTIONS]
```

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--prompt` | (required) | Text description of the image |
| `--profile NAME` | (none) | Image size profile (21 presets — run `list-profiles`) |
| `--style NAME` | (none) | AI style preset (20 options — run `list-styles`) |
| `--filter NAME` | (none) | Post-processing color filter (15 options — run `list-filters`) |
| `--seed NUMBER` | random | Reproducibility seed |
| `--width NUMBER` | 1024 | Generation width (snapped to nearest 64) |
| `--height NUMBER` | 1024 | Generation height (snapped to nearest 64) |
| `--steps NUMBER` | 4 | Sampling steps |
| `--cfg NUMBER` | 1.0 | CFG scale |
| `--format` | avif | Output format: `avif`, `webp`, `jpg`, `png` |
| `--quality` | 85 | Compression quality 0-100 |
| `--speed` | 6 | AVIF encoding speed 0-10 (0=best compression) |
| `--lossless` | off | Lossless compression (AVIF/WebP) |
| `--subsampling` | auto | Chroma: `4:4:4`, `4:2:2`, `4:2:0` |
| `--resize WxH` | (none) | Resize output (e.g., `800x600`). Lanczos |
| `--scale FACTOR` | (none) | Scale output (e.g., `0.5` = half size) |
| `--crop WxH` | (none) | Crop output (e.g., `800x600`) |
| `--crop-gravity` | center | Crop anchor: `center`, `top`, `bottom`, `left`, `right` |
| `--output-dir` | /tmp/comfyui-output | Save directory |

## Profiles (21 presets)

| Category | Profile | Size | Aspect |
|----------|---------|------|--------|
| Heroes | `hero-wide` | 1024x384 | 2.7:1 |
| | `hero-home` | 1024x576 | 16:9 |
| | `hero-tall` | 1024x768 | 4:3 |
| Cards | `card-wide` | 1024x512 | 2:1 |
| | `card-landscape` | 1024x576 | 16:9 |
| | `card-4x3` | 1024x768 | 4:3 |
| | `card-square` | 1024x1024 | 1:1 |
| Thumbnails | `thumbnail` | 512x512 | 1:1 |
| | `thumbnail-wide` | 768x512 | 3:2 |
| Portraits | `portrait` | 768x1024 | 3:4 |
| | `portrait-tall` | 576x1024 | 9:16 |
| | `portrait-full` | 768x1344 | 4:7 |
| Social | `og-image` | 1024x576 | 16:9 |
| | `social-square` | 1024x1024 | 1:1 |
| | `instagram-post` | 1024x1024 | 1:1 |
| | `instagram-story` | 576x1024 | 9:16 |
| | `pinterest` | 768x1152 | 2:3 |
| | `facebook-cover` | 1024x384 | 2.7:1 |
| | `linkedin` | 1024x576 | 16:9 |
| Backgrounds | `background` | 1024x576 | 16:9 |
| | `background-tall` | 1024x1024 | 1:1 |

## Styles (20 presets) — modify AI generation prompt

`photo`, `cinematic`, `editorial`, `product`, `architectural`, `aerial`, `headshot`, `food`, `illustration`, `watercolor`, `oil-painting`, `sketch`, `flat`, `3d`, `anime`, `vintage`, `minimalist`, `abstract`, `noir`, `fantasy`

## Filters (15 presets) — post-processing color grading

| Filter | Effect |
|--------|--------|
| `warm` | Warm golden tones |
| `cool` | Cool blue tones |
| `vivid` | Boosted saturation |
| `muted` | Soft desaturated |
| `sepia` | Classic sepia tone |
| `bw` | Black & white |
| `high-contrast` | Punchy contrast |
| `soft` | Dreamy soft focus |
| `vintage` | Faded retro film |
| `dramatic` | High contrast moody |
| `fade` | Lifted blacks (matte) |
| `golden` | Golden hour warmth |
| `arctic` | Cold blue |
| `noir` | Dark film noir B&W |
| `grain` | Film grain texture |

## Examples

```bash
# Hero banner with cinematic style and warm filter
python3 .claude/skills/comfyui/generate.py --prompt "modern office" --profile hero-home --style cinematic --filter warm

# Product card, high quality AVIF
python3 .claude/skills/comfyui/generate.py --prompt "luxury watch" --profile card-4x3 --style product --quality 95

# Portrait with vintage look, resized for web
python3 .claude/skills/comfyui/generate.py --prompt "professional headshot" --profile portrait --style headshot --filter vintage --resize 400x533

# Social media with crop
python3 .claude/skills/comfyui/generate.py --prompt "food spread" --profile social-square --style food --crop 800x800

# Check API status
python3 .claude/skills/comfyui/generate.py status

# Check dependencies (Pillow, AVIF)
python3 .claude/skills/comfyui/generate.py check-deps
```

## Rules

- ONLY run `python3 .claude/skills/comfyui/generate.py`. Nothing else.
- NEVER run curl, kubectl, or any other commands.
- NEVER manually construct JSON workflows.
- Output is AVIF by default — commit `.avif` files directly to the repo.
- Report the output file paths from the JSON result.
- Run `check-deps` first if format conversion fails.
