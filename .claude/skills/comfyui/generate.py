#!/usr/bin/env python3
"""Self-contained ComfyUI image generator.

Embeds the Z-Image Turbo workflow template, profiles, workflow builder,
and API client. No external file dependencies — just Python stdlib + optional Pillow.

Usage:
    python3 generate.py --prompt "a sunset" [--profile hero-home] [--seed 42] [--format avif]
    python3 generate.py status
    python3 generate.py list-models
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# Embedded Z-Image Turbo workflow template
# ---------------------------------------------------------------------------
ZIMAGE_TURBO_TEMPLATE = {
    "1": {
        "class_type": "UNETLoader",
        "inputs": {
            "unet_name": "z_image_turbo_bf16.safetensors",
            "weight_dtype": "default",
        },
    },
    "2": {
        "class_type": "CLIPLoader",
        "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2"},
    },
    "3": {
        "class_type": "VAELoader",
        "inputs": {"vae_name": "ae.safetensors"},
    },
    "4": {
        "class_type": "CLIPTextEncode",
        "inputs": {"text": "a beautiful landscape", "clip": ["2", 0]},
    },
    "5": {
        "class_type": "ModelSamplingAuraFlow",
        "inputs": {"shift": 3, "model": ["1", 0]},
    },
    "6": {
        "class_type": "ConditioningZeroOut",
        "inputs": {"conditioning": ["4", 0]},
    },
    "7": {
        "class_type": "EmptySD3LatentImage",
        "inputs": {"width": 1024, "height": 1024, "batch_size": 1},
    },
    "8": {
        "class_type": "KSampler",
        "inputs": {
            "seed": 0,
            "steps": 4,
            "cfg": 1.0,
            "sampler_name": "res_multistep",
            "scheduler": "simple",
            "denoise": 1.0,
            "model": ["5", 0],
            "positive": ["4", 0],
            "negative": ["6", 0],
            "latent_image": ["7", 0],
        },
    },
    "9": {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["8", 0], "vae": ["3", 0]},
    },
    "10": {
        "class_type": "SaveImage",
        "inputs": {"filename_prefix": "comfyui", "images": ["9", 0]},
    },
}

# ---------------------------------------------------------------------------
# Embedded profiles
# ---------------------------------------------------------------------------
PROFILES = {
    "hero-home": {
        "description": "Homepage hero banner (16:9)",
        "gen_width": 1024,
        "gen_height": 576,
        "steps": 4,
        "cfg": 1.0,
    },
    "card-4x3": {
        "description": "Card image (4:3)",
        "gen_width": 1024,
        "gen_height": 768,
        "steps": 4,
        "cfg": 1.0,
    },
    "social-square": {
        "description": "Social media square (1:1)",
        "gen_width": 1024,
        "gen_height": 1024,
        "steps": 4,
        "cfg": 1.0,
    },
}


# ---------------------------------------------------------------------------
# Workflow builder
# ---------------------------------------------------------------------------
def find_nodes_by_class(workflow: dict, class_type: str) -> list:
    results = []
    for node_id, node in workflow.items():
        if node.get("class_type") == class_type:
            results.append((node_id, node))
    return results


def build_workflow(prompt, seed=None, steps=None, cfg=None, width=None, height=None):
    wf = json.loads(json.dumps(ZIMAGE_TURBO_TEMPLATE))

    # Inject prompt
    clip_nodes = find_nodes_by_class(wf, "CLIPTextEncode")
    clip_nodes.sort(key=lambda x: int(x[0]) if x[0].isdigit() else x[0])
    if clip_nodes:
        clip_nodes[0][1]["inputs"]["text"] = prompt

    # Inject sampler params
    for _, node in find_nodes_by_class(wf, "KSampler"):
        if seed is not None:
            node["inputs"]["seed"] = seed
        if steps is not None:
            node["inputs"]["steps"] = steps
        if cfg is not None:
            node["inputs"]["cfg"] = cfg

    # Inject latent dimensions
    for ct in ("EmptyLatentImage", "EmptyFlux2LatentImage", "EmptySD3LatentImage"):
        for _, node in find_nodes_by_class(wf, ct):
            if width is not None:
                node["inputs"]["width"] = width
            if height is not None:
                node["inputs"]["height"] = height

    return wf


# ---------------------------------------------------------------------------
# API client
# ---------------------------------------------------------------------------
def submit_prompt(base_url, payload):
    url = f"{base_url}/prompt"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    prompt_id = result.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"No prompt_id in response: {result}")
    return prompt_id


def poll_history(base_url, prompt_id, timeout=120, interval=2):
    url = f"{base_url}/history/{prompt_id}"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url) as resp:
                history = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError:
            time.sleep(interval)
            continue
        if prompt_id in history:
            entry = history[prompt_id]
            status = entry.get("status", {})
            if status.get("completed", False):
                return entry
            if status.get("status_str") == "error":
                raise RuntimeError(f"ComfyUI error: {status}")
        time.sleep(interval)
    raise TimeoutError(f"Prompt {prompt_id} did not complete within {timeout}s")


def extract_output_files(history_entry):
    files = []
    for _node_id, node_output in history_entry.get("outputs", {}).items():
        for key in ("images", "gifs"):
            for item in node_output.get(key, []):
                files.append(item)
    return files


def download_file(base_url, file_info, output_dir, output_format="png"):
    params = urllib.parse.urlencode({
        "filename": file_info["filename"],
        "subfolder": file_info.get("subfolder", ""),
        "type": file_info.get("type", "output"),
    })
    url = f"{base_url}/view?{params}"
    dest = os.path.join(output_dir, file_info["filename"])
    urllib.request.urlretrieve(url, dest)

    if output_format != "png" and dest.lower().endswith(".png"):
        try:
            from PIL import Image

            try:
                import pillow_avif  # noqa: F401
            except ImportError:
                pass
            ext_map = {"webp": ".webp", "jpg": ".jpg", "jpeg": ".jpg", "avif": ".avif"}
            ext = ext_map.get(output_format, f".{output_format}")
            converted = dest.rsplit(".", 1)[0] + ext
            save_kwargs = {}
            if output_format in ("webp", "avif"):
                save_kwargs["quality"] = 85
            elif output_format in ("jpg", "jpeg"):
                save_kwargs["quality"] = 90
            img = Image.open(dest)
            img.save(converted, **save_kwargs)
            os.remove(dest)
            return converted
        except ImportError:
            print("WARNING: Pillow not installed, keeping PNG format", file=sys.stderr)
    return dest


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------
def cmd_status(base_url):
    try:
        with urllib.request.urlopen(f"{base_url}/system_stats") as resp:
            d = json.loads(resp.read().decode("utf-8"))
        dev = d["devices"][0]
        print("ComfyUI: ONLINE")
        print(f'  GPU: {dev["name"]}')
        print(f'  VRAM total: {dev["vram_total"] // 1048576}MB')
        print(f'  VRAM free:  {dev["vram_free"] // 1048576}MB')
    except Exception:
        print(f"ComfyUI: OFFLINE (unreachable at {base_url})")
        sys.exit(1)


def cmd_list_models(base_url):
    try:
        with urllib.request.urlopen(f"{base_url}/models/checkpoints") as resp:
            models = json.loads(resp.read().decode("utf-8"))
        print("Available checkpoints:")
        for m in models:
            print(f"  {m}")
        if not models:
            print("  (none)")
    except Exception:
        print(f"ERROR: ComfyUI not reachable at {base_url}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate images via ComfyUI (Z-Image Turbo 6B)."
    )
    parser.add_argument("prompt_or_cmd", nargs="?", default=None,
                        help="Prompt text, or 'status' / 'list-models'")
    parser.add_argument("--prompt", default=None, help="Prompt text (alternative to positional)")
    parser.add_argument("--profile", default=None, choices=list(PROFILES.keys()),
                        help="Output profile (hero-home, card-4x3, social-square)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--width", type=int, default=None, help="Image width")
    parser.add_argument("--height", type=int, default=None, help="Image height")
    parser.add_argument("--steps", type=int, default=None, help="Sampling steps (default: 4)")
    parser.add_argument("--cfg", type=float, default=None, help="CFG scale (default: 1.0)")
    parser.add_argument("--format", default="avif", choices=["png", "webp", "jpg", "avif"],
                        help="Output format (default: avif)")
    parser.add_argument("--output-dir", default="/tmp/comfyui-output",
                        help="Directory for output files")
    parser.add_argument("--url", default="https://api.studio.hardmagic.com",
                        help="ComfyUI API URL")
    parser.add_argument("--timeout", type=int, default=120, help="Max wait seconds")
    args = parser.parse_args()

    # Handle subcommands
    if args.prompt_or_cmd == "status":
        cmd_status(args.url)
        return
    if args.prompt_or_cmd == "list-models":
        cmd_list_models(args.url)
        return

    # Resolve prompt
    prompt = args.prompt or args.prompt_or_cmd
    if not prompt:
        parser.error("prompt is required")

    # Apply profile defaults
    width, height, steps, cfg = args.width, args.height, args.steps, args.cfg
    if args.profile:
        p = PROFILES[args.profile]
        if width is None:
            width = p["gen_width"]
        if height is None:
            height = p["gen_height"]
        if steps is None:
            steps = p["steps"]
        if cfg is None:
            cfg = p["cfg"]

    # Build workflow
    workflow = build_workflow(prompt, seed=args.seed, steps=steps, cfg=cfg,
                             width=width, height=height)
    payload = {"prompt": workflow}

    os.makedirs(args.output_dir, exist_ok=True)

    # Submit
    print(f"Submitting to {args.url} ...", file=sys.stderr)
    prompt_id = submit_prompt(args.url, payload)
    print(f"Prompt ID: {prompt_id}", file=sys.stderr)

    # Poll
    print("Waiting for completion ...", file=sys.stderr)
    entry = poll_history(args.url, prompt_id, timeout=args.timeout)
    print("Generation complete.", file=sys.stderr)

    # Download
    output_files = extract_output_files(entry)
    downloaded = []
    for finfo in output_files:
        dest = download_file(args.url, finfo, args.output_dir, output_format=args.format)
        downloaded.append(dest)
        print(f"Saved: {dest}", file=sys.stderr)

    # JSON summary to stdout
    summary = {
        "prompt_id": prompt_id,
        "files": downloaded,
        "output_dir": os.path.abspath(args.output_dir),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
