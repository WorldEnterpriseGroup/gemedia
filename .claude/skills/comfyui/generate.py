#!/usr/bin/env python3
"""Self-contained ComfyUI image generator.

Embeds Z-Image Turbo workflow, 20+ profiles, 20 style presets, 15 post-processing
filters, full AVIF/WebP/JPEG controls, scaling, cropping, and resize.
Python stdlib + Pillow (for format conversion and filters).

Usage:
    python3 generate.py --prompt "a sunset" --style cinematic --profile hero-home
    python3 generate.py --prompt "headshot" --profile portrait --filter golden
    python3 generate.py --prompt "logo" --profile thumbnail --format avif --lossless
    python3 generate.py check-deps
    python3 generate.py list-profiles
    python3 generate.py list-styles
    python3 generate.py list-filters
    python3 generate.py status
"""

import argparse
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


# ---------------------------------------------------------------------------
# Embedded Z-Image Turbo workflow template
# Model: Z-Image Turbo 6B — 4 steps, ~6s/image on RTX 3090
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
# Profiles — 21 common web image sizes
# All gen dimensions are multiples of 64 for optimal diffusion model output.
# ---------------------------------------------------------------------------
PROFILES = {
    # Heroes & Banners
    "hero-wide":       {"w": 1024, "h": 384,  "desc": "Ultra-wide hero / Facebook cover (≈2.7:1)"},
    "hero-home":       {"w": 1024, "h": 576,  "desc": "Standard hero banner (16:9)"},
    "hero-tall":       {"w": 1024, "h": 768,  "desc": "Tall hero section (4:3)"},
    # Cards
    "card-wide":       {"w": 1024, "h": 512,  "desc": "Wide card / email header (2:1)"},
    "card-landscape":  {"w": 1024, "h": 576,  "desc": "Landscape card (16:9)"},
    "card-4x3":        {"w": 1024, "h": 768,  "desc": "Standard card (4:3)"},
    "card-square":     {"w": 1024, "h": 1024, "desc": "Square card (1:1)"},
    # Thumbnails
    "thumbnail":       {"w": 512,  "h": 512,  "desc": "Small thumbnail (1:1)"},
    "thumbnail-wide":  {"w": 768,  "h": 512,  "desc": "Wide thumbnail (3:2)"},
    # Portraits
    "portrait":        {"w": 768,  "h": 1024, "desc": "Portrait / headshot (3:4)"},
    "portrait-tall":   {"w": 576,  "h": 1024, "desc": "Tall portrait (9:16)"},
    "portrait-full":   {"w": 768,  "h": 1344, "desc": "Full-length portrait (≈4:7)"},
    # Social Media
    "og-image":        {"w": 1024, "h": 576,  "desc": "Open Graph / Twitter Card (≈1.91:1)"},
    "social-square":   {"w": 1024, "h": 1024, "desc": "Social media square (1:1)"},
    "instagram-post":  {"w": 1024, "h": 1024, "desc": "Instagram post (1:1)"},
    "instagram-story": {"w": 576,  "h": 1024, "desc": "Instagram / TikTok story (9:16)"},
    "pinterest":       {"w": 768,  "h": 1152, "desc": "Pinterest pin (2:3)"},
    "facebook-cover":  {"w": 1024, "h": 384,  "desc": "Facebook cover photo (≈2.7:1)"},
    "linkedin":        {"w": 1024, "h": 576,  "desc": "LinkedIn post image (16:9)"},
    # Backgrounds
    "background":      {"w": 1024, "h": 576,  "desc": "Background image (16:9)"},
    "background-tall": {"w": 1024, "h": 1024, "desc": "Square background / texture (1:1)"},
}


# ---------------------------------------------------------------------------
# Styles — prompt modifiers for different visual aesthetics
# Applied as suffix to the user's prompt to steer the model.
# ---------------------------------------------------------------------------
STYLES = {
    "photo":          "professional photography, photorealistic, natural lighting, sharp focus, high detail",
    "cinematic":      "cinematic still, dramatic lighting, film grain, anamorphic lens, movie scene",
    "editorial":      "editorial photography, magazine quality, soft lighting, elegant composition",
    "product":        "product photography, studio lighting, clean white background, commercial quality",
    "architectural":  "architectural photography, clean lines, dramatic perspective, professional",
    "aerial":         "aerial photography, drone shot, bird's eye view, sweeping landscape",
    "headshot":       "portrait photography, soft bokeh background, studio lighting, professional headshot",
    "food":           "food photography, appetizing, soft natural lighting, shallow depth of field",
    "illustration":   "digital illustration, clean lines, vibrant colors, modern illustration style",
    "watercolor":     "watercolor painting, soft washes, organic textures, artistic, hand-painted",
    "oil-painting":   "oil painting, thick impasto brushstrokes, rich colors, classical fine art",
    "sketch":         "pencil sketch, detailed line drawing, cross-hatching, hand-drawn on paper",
    "flat":           "flat design, minimal, vector-style, clean geometric shapes, solid colors",
    "3d":             "3D render, octane render, studio lighting, photorealistic CGI, ray-traced",
    "anime":          "anime style, high quality anime illustration, detailed cel-shaded",
    "vintage":        "vintage photograph, retro film, faded colors, light leaks, nostalgic 1970s",
    "minimalist":     "minimalist, clean composition, ample negative space, elegant simplicity",
    "abstract":       "abstract art, bold colors, geometric shapes, contemporary modern art",
    "noir":           "film noir, high contrast black and white, dramatic shadows, moody atmosphere",
    "fantasy":        "fantasy art, magical atmosphere, ethereal lighting, epic detailed, concept art",
}


# ---------------------------------------------------------------------------
# Filters — Instagram-style post-processing color grading
# Each filter is a dict describing PIL operations to apply.
# Operations: brightness, contrast, saturation, color_temp, sepia, grayscale,
#             vignette, grain, fade, hue_shift, sharpen
# ---------------------------------------------------------------------------
FILTERS = {
    "warm":          {"desc": "Warm golden tones",           "color_temp": 30,  "saturation": 1.1},
    "cool":          {"desc": "Cool blue tones",             "color_temp": -30, "saturation": 1.05},
    "vivid":         {"desc": "Boosted saturation & color",  "saturation": 1.4, "contrast": 1.15},
    "muted":         {"desc": "Soft desaturated tones",      "saturation": 0.6, "contrast": 0.95},
    "sepia":         {"desc": "Classic warm sepia tone",     "sepia": True,     "saturation": 0.8},
    "bw":            {"desc": "Black & white",               "grayscale": True, "contrast": 1.1},
    "high-contrast": {"desc": "Punchy high contrast",        "contrast": 1.4,   "saturation": 1.05},
    "soft":          {"desc": "Dreamy soft focus",           "contrast": 0.85,  "brightness": 1.05, "sharpen": -1},
    "vintage":       {"desc": "Faded retro film look",       "saturation": 0.7, "contrast": 0.9, "fade": 20, "color_temp": 15},
    "dramatic":      {"desc": "High contrast, moody",        "contrast": 1.3,   "saturation": 0.85, "brightness": 0.95},
    "fade":          {"desc": "Lifted blacks, matte look",   "fade": 35, "contrast": 0.9},
    "golden":        {"desc": "Golden hour warmth",          "color_temp": 40, "saturation": 1.15, "brightness": 1.05},
    "arctic":        {"desc": "Cold blue, desaturated",      "color_temp": -40, "saturation": 0.7, "brightness": 1.05},
    "noir":          {"desc": "Dark film noir B&W",          "grayscale": True, "contrast": 1.5, "brightness": 0.9},
    "grain":         {"desc": "Subtle film grain texture",   "grain": 15, "saturation": 0.95},
}


def apply_filter(img, filter_name):
    """Apply an Instagram-style filter to a PIL Image. Returns modified image.

    Uses numpy for fast pixel operations when available, falls back to
    PIL-only operations otherwise.
    """
    from PIL import Image, ImageEnhance, ImageFilter

    if filter_name not in FILTERS:
        print(f"WARNING: Unknown filter '{filter_name}', skipping", file=sys.stderr)
        return img

    ops = FILTERS[filter_name]
    img = img.convert("RGB")

    # Try numpy for fast pixel ops
    try:
        import numpy as np
        use_numpy = True
    except ImportError:
        use_numpy = False

    # Brightness (PIL fast path)
    if "brightness" in ops:
        img = ImageEnhance.Brightness(img).enhance(ops["brightness"])

    # Contrast (PIL fast path)
    if "contrast" in ops:
        img = ImageEnhance.Contrast(img).enhance(ops["contrast"])

    # Saturation (PIL fast path)
    if "saturation" in ops:
        img = ImageEnhance.Saturation(img).enhance(ops["saturation"])

    # Color temperature shift (warm = positive/orange, cool = negative/blue)
    if "color_temp" in ops:
        shift = ops["color_temp"]
        if use_numpy:
            arr = np.array(img, dtype=np.int16)
            arr[:, :, 0] = np.clip(arr[:, :, 0] + shift, 0, 255)  # R
            arr[:, :, 2] = np.clip(arr[:, :, 2] - shift, 0, 255)  # B
            img = Image.fromarray(arr.astype(np.uint8))
        else:
            r, g, b = img.split()
            r = r.point(lambda p: min(255, max(0, p + shift)))
            b = b.point(lambda p: min(255, max(0, p - shift)))
            img = Image.merge("RGB", (r, g, b))

    # Sepia tone
    if ops.get("sepia"):
        if use_numpy:
            arr = np.array(img, dtype=np.float32)
            gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
            arr[:, :, 0] = np.clip(gray * 1.2, 0, 255)
            arr[:, :, 1] = np.clip(gray * 1.0, 0, 255)
            arr[:, :, 2] = np.clip(gray * 0.8, 0, 255)
            img = Image.fromarray(arr.astype(np.uint8))
        else:
            img = img.convert("L")
            r = img.point(lambda p: min(255, int(p * 1.2)))
            g = img.copy()
            b = img.point(lambda p: min(255, int(p * 0.8)))
            img = Image.merge("RGB", (r, g, b))

    # Grayscale
    if ops.get("grayscale"):
        img = img.convert("L").convert("RGB")

    # Fade (lift blacks — add constant to all channels)
    if "fade" in ops:
        fade_val = ops["fade"]
        if use_numpy:
            arr = np.array(img, dtype=np.int16)
            arr = np.clip(arr + fade_val, 0, 255)
            img = Image.fromarray(arr.astype(np.uint8))
        else:
            img = img.point(lambda p: min(255, p + fade_val))

    # Sharpen (positive) or blur (negative)
    if "sharpen" in ops:
        if ops["sharpen"] > 0:
            img = img.filter(ImageFilter.SHARPEN)
        else:
            img = img.filter(ImageFilter.GaussianBlur(radius=1.5))

    # Film grain (add random noise)
    if "grain" in ops:
        intensity = ops["grain"]
        w, h = img.size
        if use_numpy:
            rng = np.random.RandomState(42)
            noise = rng.randint(-intensity, intensity + 1, (h, w, 3), dtype=np.int16)
            arr = np.array(img, dtype=np.int16)
            arr = np.clip(arr + noise, 0, 255)
            img = Image.fromarray(arr.astype(np.uint8))
        else:
            rand = random.Random(42)
            pixels = img.load()
            for y in range(h):
                for x in range(w):
                    noise = rand.randint(-intensity, intensity)
                    r, g, b = pixels[x, y]
                    pixels[x, y] = (
                        min(255, max(0, r + noise)),
                        min(255, max(0, g + noise)),
                        min(255, max(0, b + noise)),
                    )

    print(f"  Filter: {filter_name} ({ops['desc']})", file=sys.stderr)
    return img


# ---------------------------------------------------------------------------
# Dependency checking
# ---------------------------------------------------------------------------
def check_dependencies():
    """Check for Pillow and AVIF support. Returns dict of status info."""
    info = {
        "python": sys.version.split()[0],
        "pillow": None,
        "avif": False,
        "avif_source": None,
        "webp": False,
    }

    try:
        from PIL import Image
        info["pillow"] = Image.__version__

        # Check AVIF support
        # Method 1: native Pillow AVIF (10.1+)
        if "AVIF" in Image.registered_extensions().values():
            info["avif"] = True
            info["avif_source"] = "pillow-native"
        else:
            # Method 2: pillow-avif-plugin
            try:
                import pillow_avif  # noqa: F401
                info["avif"] = True
                info["avif_source"] = "pillow-avif-plugin"
            except ImportError:
                pass

        # Check WebP
        if "WEBP" in Image.registered_extensions().values():
            info["webp"] = True

    except ImportError:
        pass

    return info


def cmd_check_deps():
    """Print dependency status and install hints."""
    info = check_dependencies()

    print("=== ComfyUI Generator Dependencies ===\n")
    print(f"  Python:  {info['python']}")

    if info["pillow"]:
        print(f"  Pillow:  {info['pillow']} ✓")
    else:
        print("  Pillow:  NOT INSTALLED ✗")
        print("           pip install Pillow")
        print("           (required for AVIF/WebP/JPEG conversion, resize, crop)")

    if info["avif"]:
        print(f"  AVIF:    supported via {info['avif_source']} ✓")
    else:
        print("  AVIF:    NOT AVAILABLE ✗")
        if info["pillow"]:
            v = tuple(int(x) for x in info["pillow"].split(".")[:2])
            if v < (10, 1):
                print("           pip install pillow-avif-plugin")
                print(f"           (or upgrade Pillow to 10.1+, you have {info['pillow']})")
            else:
                print("           Pillow 10.1+ detected but AVIF codec not found.")
                print("           Install libavif system library, then reinstall Pillow:")
                print("             apt install libavif-dev && pip install --force-reinstall Pillow")
        else:
            print("           pip install Pillow pillow-avif-plugin")

    if info["webp"]:
        print("  WebP:    supported ✓")
    else:
        print("  WebP:    NOT AVAILABLE ✗")

    print()
    if info["pillow"] and info["avif"]:
        print("  All dependencies satisfied. AVIF output ready.")
    elif info["pillow"]:
        print("  Pillow installed but AVIF not available.")
        print("  Output will fall back to PNG unless you install AVIF support.")
    else:
        print("  Pillow not installed. Install it for format conversion:")
        print("    pip install Pillow pillow-avif-plugin")
        print("  Without Pillow, output will be PNG only.")

    return info


# ---------------------------------------------------------------------------
# Image post-processing (format conversion, resize, crop, scale)
# ---------------------------------------------------------------------------
def snap_to_multiple(val, multiple=64):
    """Snap a dimension to the nearest multiple (for diffusion model compatibility)."""
    return max(multiple, round(val / multiple) * multiple)


def _get_pillow():
    """Import and return PIL.Image, registering AVIF if needed. Returns None if unavailable."""
    try:
        from PIL import Image
        try:
            import pillow_avif  # noqa: F401
        except ImportError:
            pass
        return Image
    except ImportError:
        return None


def postprocess_image(filepath, output_format="avif", quality=85, speed=6,
                      lossless=False, subsampling=None,
                      resize=None, scale=None, crop=None, filter_name=None):
    """Apply post-processing to a downloaded image.

    Args:
        filepath: Path to the downloaded PNG file
        output_format: Target format (avif, webp, jpg, png)
        quality: Compression quality 0-100 (ignored if lossless)
        speed: AVIF encoding speed 0-10 (0=best compression, 10=fastest)
        lossless: If True, use lossless compression
        subsampling: Chroma subsampling (4:4:4, 4:2:2, 4:2:0) — None for auto
        resize: Tuple (width, height) to resize to
        scale: Float scale factor (0.5 = half size, 2.0 = double)
        crop: Tuple (width, height, gravity) where gravity is center/top/bottom/left/right
        filter_name: Name of an Instagram-style color filter to apply

    Returns:
        Path to the processed output file.
    """
    Image = _get_pillow()
    if Image is None:
        if output_format != "png" or resize or scale or crop:
            print("WARNING: Pillow not installed. Skipping post-processing.", file=sys.stderr)
            print("  Install: pip install Pillow pillow-avif-plugin", file=sys.stderr)
        return filepath

    img = Image.open(filepath)

    # Apply color filter first (before geometric transforms)
    if filter_name:
        img = apply_filter(img, filter_name)

    # Apply crop (before resize/scale, so dimensions are predictable)
    if crop:
        crop_w, crop_h, gravity = crop
        img_w, img_h = img.size

        # Calculate crop box based on gravity
        if gravity == "center":
            left = max(0, (img_w - crop_w) // 2)
            top = max(0, (img_h - crop_h) // 2)
        elif gravity == "top":
            left = max(0, (img_w - crop_w) // 2)
            top = 0
        elif gravity == "bottom":
            left = max(0, (img_w - crop_w) // 2)
            top = max(0, img_h - crop_h)
        elif gravity == "left":
            left = 0
            top = max(0, (img_h - crop_h) // 2)
        elif gravity == "right":
            left = max(0, img_w - crop_w)
            top = max(0, (img_h - crop_h) // 2)
        else:
            left = max(0, (img_w - crop_w) // 2)
            top = max(0, (img_h - crop_h) // 2)

        right = min(img_w, left + crop_w)
        bottom = min(img_h, top + crop_h)
        img = img.crop((left, top, right, bottom))
        print(f"  Cropped to {right - left}x{bottom - top} (gravity: {gravity})", file=sys.stderr)

    # Apply scale
    if scale and scale != 1.0:
        new_w = max(1, round(img.size[0] * scale))
        new_h = max(1, round(img.size[1] * scale))
        img = img.resize((new_w, new_h), Image.LANCZOS)
        print(f"  Scaled {scale}x → {new_w}x{new_h}", file=sys.stderr)

    # Apply resize (exact dimensions)
    if resize:
        img = img.resize(resize, Image.LANCZOS)
        print(f"  Resized to {resize[0]}x{resize[1]}", file=sys.stderr)

    # Determine output path
    if output_format == "png" and not resize and not scale and not crop and not filter_name:
        return filepath  # No conversion needed

    ext_map = {"webp": ".webp", "jpg": ".jpg", "jpeg": ".jpg", "avif": ".avif", "png": ".png"}
    ext = ext_map.get(output_format, f".{output_format}")
    output_path = filepath.rsplit(".", 1)[0] + ext

    # Build save kwargs based on format
    save_kwargs = {}

    if output_format == "avif":
        if lossless:
            save_kwargs["quality"] = -1
        else:
            save_kwargs["quality"] = quality
        save_kwargs["speed"] = speed
        if subsampling:
            save_kwargs["subsampling"] = subsampling

    elif output_format == "webp":
        save_kwargs["quality"] = quality
        save_kwargs["lossless"] = lossless
        save_kwargs["method"] = min(6, max(0, 6 - speed))  # invert: 0=fast, 6=best

    elif output_format in ("jpg", "jpeg"):
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True
        if subsampling:
            # Pillow JPEG subsampling: 0=4:4:4, 1=4:2:2, 2=4:2:0
            sub_map = {"4:4:4": 0, "4:2:2": 1, "4:2:0": 2}
            if subsampling in sub_map:
                save_kwargs["subsampling"] = sub_map[subsampling]
        # Convert RGBA to RGB for JPEG
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

    img.save(output_path, **save_kwargs)

    # Report compression stats
    orig_size = os.path.getsize(filepath)
    new_size = os.path.getsize(output_path)
    ratio = (1 - new_size / orig_size) * 100 if orig_size > 0 else 0
    fmt_label = f"{output_format.upper()}"
    if lossless:
        fmt_label += " (lossless)"
    print(f"  {fmt_label}: {new_size:,} bytes ({ratio:.0f}% smaller than PNG)", file=sys.stderr)

    # Remove original PNG if we converted to a different format
    if output_path != filepath and os.path.exists(filepath):
        os.remove(filepath)

    return output_path


# ---------------------------------------------------------------------------
# Workflow builder
# ---------------------------------------------------------------------------
def find_nodes_by_class(workflow, class_type):
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


def download_file(base_url, file_info, output_dir):
    """Download a raw output file from ComfyUI. Returns local path."""
    params = urllib.parse.urlencode({
        "filename": file_info["filename"],
        "subfolder": file_info.get("subfolder", ""),
        "type": file_info.get("type", "output"),
    })
    url = f"{base_url}/view?{params}"
    dest = os.path.join(output_dir, file_info["filename"])
    urllib.request.urlretrieve(url, dest)
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


def cmd_list_profiles():
    print("Available profiles:\n")
    # Group by category
    categories = {
        "Heroes & Banners": ["hero-wide", "hero-home", "hero-tall"],
        "Cards": ["card-wide", "card-landscape", "card-4x3", "card-square"],
        "Thumbnails": ["thumbnail", "thumbnail-wide"],
        "Portraits": ["portrait", "portrait-tall", "portrait-full"],
        "Social Media": ["og-image", "social-square", "instagram-post",
                         "instagram-story", "pinterest", "facebook-cover", "linkedin"],
        "Backgrounds": ["background", "background-tall"],
    }
    for cat, names in categories.items():
        print(f"  {cat}:")
        for name in names:
            p = PROFILES[name]
            print(f"    {name:20s} {p['w']:4d}x{p['h']:<4d}  {p['desc']}")
        print()


def cmd_list_styles():
    print("Available styles (--style):\n")
    print("  Styles modify the PROMPT to steer the AI model's aesthetic.\n")
    for name, suffix in sorted(STYLES.items()):
        display = suffix[:65] + "..." if len(suffix) > 65 else suffix
        print(f"  {name:16s}  {display}")
    print(f"\nUsage: --style {list(STYLES.keys())[0]}")


def cmd_list_filters():
    print("Available filters (--filter):\n")
    print("  Filters apply POST-PROCESSING color grading to the output image.\n")
    categories = {
        "Color Temperature": ["warm", "cool", "golden", "arctic"],
        "Tone & Mood": ["vivid", "muted", "dramatic", "soft", "high-contrast"],
        "Film & Retro": ["vintage", "sepia", "fade", "grain"],
        "Black & White": ["bw", "noir"],
    }
    for cat, names in categories.items():
        print(f"  {cat}:")
        for name in names:
            f = FILTERS[name]
            print(f"    {name:16s}  {f['desc']}")
        print()
    print("Usage: --filter warm")
    print("Combine with --style for full control: --style cinematic --filter golden")


def parse_dimensions(dim_str):
    """Parse 'WIDTHxHEIGHT' string into (width, height) tuple."""
    parts = dim_str.lower().split("x")
    if len(parts) != 2:
        raise ValueError(f"Invalid dimensions '{dim_str}'. Use WIDTHxHEIGHT (e.g., 800x600)")
    return int(parts[0]), int(parts[1])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate images via ComfyUI (Z-Image Turbo 6B).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Subcommands:
  status          Check if ComfyUI API is reachable
  list-models     List available models on the server
  list-profiles   Show all 21 image size profiles
  list-styles     Show all 20 style presets (modify prompt)
  list-filters    Show all 15 color filters (post-processing)
  check-deps      Verify Pillow, AVIF, and WebP support

Examples:
  %(prog)s --prompt "a sunset" --profile hero-home --style cinematic
  %(prog)s --prompt "headshot" --profile portrait --style headshot --filter warm
  %(prog)s --prompt "product" --profile card-square --resize 600x600 --quality 90
  %(prog)s --prompt "texture" --crop 512x512 --scale 0.5 --lossless
  %(prog)s --prompt "banner" --profile hero-wide --filter golden --style editorial
""",
    )

    # Positional (for subcommands or prompt)
    parser.add_argument("prompt_or_cmd", nargs="?", default=None,
                        help="Prompt text, or subcommand (status/list-models/list-profiles/list-styles/check-deps)")

    # Prompt
    parser.add_argument("--prompt", default=None, help="Prompt text (alternative to positional arg)")

    # Style & profile
    parser.add_argument("--style", default=None, metavar="NAME",
                        help=f"Style preset: {', '.join(sorted(STYLES.keys()))}")
    parser.add_argument("--filter", default=None, metavar="NAME",
                        help=f"Color filter: {', '.join(sorted(FILTERS.keys()))}")
    parser.add_argument("--profile", default=None, metavar="NAME",
                        help="Image size profile (run list-profiles to see all)")

    # Generation params
    parser.add_argument("--seed", type=int, default=None, help="Random seed (default: random)")
    parser.add_argument("--width", type=int, default=None, help="Generation width (snapped to nearest 64)")
    parser.add_argument("--height", type=int, default=None, help="Generation height (snapped to nearest 64)")
    parser.add_argument("--steps", type=int, default=None, help="Sampling steps (default: 4)")
    parser.add_argument("--cfg", type=float, default=None, help="CFG scale (default: 1.0)")

    # Output format
    parser.add_argument("--format", default="avif", choices=["png", "webp", "jpg", "avif"],
                        help="Output image format (default: avif)")
    parser.add_argument("--quality", type=int, default=85,
                        help="Compression quality 0-100 (default: 85). Higher = better quality, larger file")
    parser.add_argument("--speed", type=int, default=6,
                        help="AVIF encoding speed 0-10 (default: 6). 0 = smallest file, 10 = fastest encode")
    parser.add_argument("--lossless", action="store_true",
                        help="Use lossless compression (AVIF/WebP only). Larger files but pixel-perfect")
    parser.add_argument("--subsampling", default=None, choices=["4:4:4", "4:2:2", "4:2:0"],
                        help="Chroma subsampling. 4:4:4 = best color, 4:2:0 = smallest file (default: auto)")

    # Post-processing
    parser.add_argument("--resize", default=None, metavar="WxH",
                        help="Resize output to exact dimensions (e.g., 800x600). Uses Lanczos resampling")
    parser.add_argument("--scale", type=float, default=None,
                        help="Scale output by factor (e.g., 0.5 = half, 2.0 = double). Uses Lanczos")
    parser.add_argument("--crop", default=None, metavar="WxH",
                        help="Crop output to dimensions (e.g., 800x600). Applied before resize/scale")
    parser.add_argument("--crop-gravity", default="center",
                        choices=["center", "top", "bottom", "left", "right"],
                        help="Crop anchor point (default: center)")

    # Output & API
    parser.add_argument("--output-dir", default="/tmp/comfyui-output",
                        help="Directory for output files (default: /tmp/comfyui-output)")
    parser.add_argument("--url", default="https://api.studio.hardmagic.com",
                        help="ComfyUI API URL")
    parser.add_argument("--timeout", type=int, default=120, help="Max wait seconds (default: 120)")

    args = parser.parse_args()

    # --- Handle subcommands ---
    cmd = args.prompt_or_cmd
    if cmd == "status":
        cmd_status(args.url)
        return
    if cmd == "list-models":
        cmd_list_models(args.url)
        return
    if cmd == "list-profiles":
        cmd_list_profiles()
        return
    if cmd == "list-styles":
        cmd_list_styles()
        return
    if cmd == "list-filters":
        cmd_list_filters()
        return
    if cmd in ("check-deps", "check"):
        cmd_check_deps()
        return

    # --- Resolve prompt ---
    prompt = args.prompt or cmd
    if not prompt:
        parser.error("prompt is required. Run with --help for usage.")

    # --- Apply style ---
    if args.style:
        if args.style not in STYLES:
            parser.error(f"Unknown style '{args.style}'. Run list-styles to see options.")
        prompt = f"{prompt}, {STYLES[args.style]}"
        print(f"Style: {args.style}", file=sys.stderr)

    # --- Validate filter ---
    if args.filter and args.filter not in FILTERS:
        parser.error(f"Unknown filter '{args.filter}'. Run list-filters to see options.")

    # --- Apply profile ---
    width, height, steps, cfg = args.width, args.height, args.steps, args.cfg
    if args.profile:
        if args.profile not in PROFILES:
            parser.error(f"Unknown profile '{args.profile}'. Run list-profiles to see options.")
        p = PROFILES[args.profile]
        if width is None:
            width = p["w"]
        if height is None:
            height = p["h"]
        print(f"Profile: {args.profile} ({p['desc']})", file=sys.stderr)

    # Snap custom dimensions to nearest 64
    if width is not None:
        width = snap_to_multiple(width, 64)
    if height is not None:
        height = snap_to_multiple(height, 64)

    # Ensure seed exists (random if not specified)
    seed = args.seed if args.seed is not None else random.randint(0, 2**32 - 1)

    # Check format dependencies before generating
    if args.format != "png" or args.resize or args.scale or args.crop or args.filter:
        info = check_dependencies()
        if not info["pillow"]:
            print("ERROR: Pillow is required for format conversion and image processing.", file=sys.stderr)
            print("  Install: pip install Pillow pillow-avif-plugin", file=sys.stderr)
            sys.exit(1)
        if args.format == "avif" and not info["avif"]:
            print("ERROR: AVIF support not available.", file=sys.stderr)
            print("  Run 'check-deps' for install instructions.", file=sys.stderr)
            sys.exit(1)
        if args.format == "webp" and not info["webp"]:
            print("ERROR: WebP support not available.", file=sys.stderr)
            sys.exit(1)

    # Parse crop/resize dimensions
    crop_dims = None
    if args.crop:
        cw, ch = parse_dimensions(args.crop)
        crop_dims = (cw, ch, args.crop_gravity)

    resize_dims = None
    if args.resize:
        resize_dims = parse_dimensions(args.resize)

    # --- Build workflow ---
    gen_w = width or 1024
    gen_h = height or 1024
    workflow = build_workflow(prompt, seed=seed, steps=steps, cfg=cfg,
                             width=gen_w, height=gen_h)
    payload = {"prompt": workflow}

    os.makedirs(args.output_dir, exist_ok=True)

    # --- Submit ---
    print(f"Generating {gen_w}x{gen_h}, seed={seed}", file=sys.stderr)
    print(f"Submitting to {args.url} ...", file=sys.stderr)
    t0 = time.monotonic()
    prompt_id = submit_prompt(args.url, payload)
    print(f"Prompt ID: {prompt_id}", file=sys.stderr)

    # --- Poll ---
    print("Waiting for completion ...", file=sys.stderr)
    entry = poll_history(args.url, prompt_id, timeout=args.timeout)
    gen_time = time.monotonic() - t0
    print(f"Generation complete in {gen_time:.1f}s", file=sys.stderr)

    # --- Download and post-process ---
    output_files = extract_output_files(entry)
    downloaded = []
    for finfo in output_files:
        raw_path = download_file(args.url, finfo, args.output_dir)
        final_path = postprocess_image(
            raw_path,
            output_format=args.format,
            quality=args.quality,
            speed=args.speed,
            lossless=args.lossless,
            subsampling=args.subsampling,
            resize=resize_dims,
            scale=args.scale,
            crop=crop_dims,
            filter_name=args.filter,
        )
        downloaded.append(final_path)
        print(f"Output: {final_path}", file=sys.stderr)

    # --- JSON summary to stdout ---
    summary = {
        "prompt_id": prompt_id,
        "seed": seed,
        "generation_time": round(gen_time, 1),
        "generated_size": f"{gen_w}x{gen_h}",
        "format": args.format,
        "files": downloaded,
        "output_dir": os.path.abspath(args.output_dir),
    }
    if args.style:
        summary["style"] = args.style
    if args.filter:
        summary["filter"] = args.filter
    if args.profile:
        summary["profile"] = args.profile
    if resize_dims:
        summary["resized_to"] = f"{resize_dims[0]}x{resize_dims[1]}"
    if args.scale:
        summary["scaled"] = args.scale
    if crop_dims:
        summary["cropped_to"] = f"{crop_dims[0]}x{crop_dims[1]}"

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
