---
name: comfyui
description: Generate images using ComfyUI Z-Image Turbo 6B (~6s/image). Outputs AVIF by default.
argument-hint: [prompt] [--profile hero-home] [--format avif] [--seed NUMBER]
allowed-tools: Bash(python3 .claude/skills/comfyui/generate.py *), Read
context: fork
---
# ComfyUI Image Generation

Generate images by running a single command. Do NOT explore, discover models, construct payloads, or deviate.

## Usage

```bash
python3 .claude/skills/comfyui/generate.py --prompt "PROMPT" [OPTIONS]
```

**Options:**
| Flag | Default | Description |
|------|---------|-------------|
| `--prompt` | (required) | Text description of the image |
| `--profile` | (none) | `hero-home` (1024x576), `card-4x3` (1024x768), `social-square` (1024x1024) |
| `--seed NUMBER` | random | Reproducibility seed |
| `--width NUMBER` | 1024 | Image width (overrides profile) |
| `--height NUMBER` | 1024 | Image height (overrides profile) |
| `--steps NUMBER` | 4 | Sampling steps |
| `--cfg NUMBER` | 1.0 | CFG scale |
| `--format` | avif | Output format: `avif`, `webp`, `jpg`, `png` |
| `--output-dir` | /tmp/comfyui-output | Save directory |

## Examples

```bash
# Hero banner
python3 .claude/skills/comfyui/generate.py --prompt "modern office interior" --profile hero-home --seed 42

# Card image
python3 .claude/skills/comfyui/generate.py --prompt "product photo" --profile card-4x3

# Check API status
python3 .claude/skills/comfyui/generate.py status
```

## Rules

- ONLY run `python3 .claude/skills/comfyui/generate.py`. Nothing else.
- NEVER run curl, kubectl, or any other commands.
- NEVER manually construct JSON workflows.
- Output is AVIF by default — commit `.avif` files directly to the repo.
- Report the output file paths from the JSON result.
