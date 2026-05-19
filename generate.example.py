#!/usr/bin/env python3
"""
Dual-provider image generator (OpenAI GPT-Image-2 + Google Gemini Nano Banana).

Runs OpenAI and Gemini in parallel where applicable and writes all results
to the current working directory.

Quickstart:
  generate.py "een logo voor Grey Matters" --concept
  generate.py "infographic over confirmation bias" --text --quality high --gemini
  generate.py "plaats deze fles op marmer met natuurlijk licht" --reference fles.jpg --gemini --quality high
  generate.py "now make it night time" --session glass-city --gemini --continue

Presets:
  --concept   dual-provider lowres concepting (2 GPT + 2 Gemini)
  --hq        single hi-quality asset (kies provider via --gpt of --gemini)
  --web       web asset, medium quality, 2 variants
  --social    portrait social media asset

Modifiers (kunnen met presets combineren):
  --text      Force Gemini Pro (beste tekst-rendering, ook bij --concept)

Provider selection (mutually exclusive):
  --gpt        OpenAI only
  --gemini     Gemini only
  (none)       dual bij --concept, anders GPT

Generic switches:
  --size square|landscape|portrait|auto
  --aspect-ratio 1:1|16:9|9:16|... (Gemini)
  --quality low|medium|high
  --resolution 512|1K|2K|4K        (Gemini only)
  --variants N                     (totaal aantal images, split in dual mode)
  --format png|jpeg|webp           (GPT only)
  --grounding                      (Gemini Google Search grounding)
  --gemini-model flash|nb2|pro|auto

Diverse varianten (cruciaal voor goede concepting):
  --prompts "p1|p2|p3|p4"          Pipe-separated lijst van unieke prompts.
                                   Vervangt de positional prompt, set --variants
                                   gelijk aan aantal entries. Bij dual worden
                                   prompts afwisselend over providers verdeeld.

Reference and edit modes (single-provider only):
  --reference IMAGE        Reference image voor composition (kan meerdere keren)
  --edit IMAGE             Pad naar bestaande image om te bewerken
  --edit-latest [DIR]      Auto-pak nieuwste image (default ~/Desktop, ~/Downloads)
  --mask IMAGE             Optionele mask (GPT only)

Multi-turn sessions (single-provider only):
  --session NAME           Start of resume een named session
  --continue               Gebruik laatst gebruikte session in deze folder
  --reset-session NAME     Verwijder een opgeslagen sessie
  --list-sessions          Toon alle sessies in deze folder

Workflow:
  --skipquestions          Geen vragen, defaults gebruiken
"""

import argparse
import base64
import copy as _copy
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path


# ============================================================================
# CONFIG: paste your API keys here, OR leave empty to use env vars
# ============================================================================
# Vul hieronder je eigen sleutels in (tussen de quotes), OF laat ze leeg en
# zet de environment variables OPENAI_API_KEY / GEMINI_API_KEY.
# LET OP: dit is het template-bestand. Kopieer het naar generate.py
# (cp generate.example.py generate.py) en vul daar je keys in. generate.py
# staat in .gitignore zodat je keys nooit per ongeluk op GitHub belanden.
OPENAI_API_KEY = ""  # bv. "sk-proj-..." — of laat leeg en zet env var OPENAI_API_KEY
GEMINI_API_KEY = ""  # bv. "AIza..."     — of laat leeg en zet env var GEMINI_API_KEY


# ============================================================================
# CONSTANTS
# ============================================================================

SIZE_TO_GPT = {
    "square":    "1024x1024",
    "landscape": "1536x1024",
    "portrait":  "1024x1536",
    "auto":      "auto",
}

SIZE_TO_GEMINI_ASPECT = {
    "square":    "1:1",
    "landscape": "16:9",
    "portrait":  "9:16",
    "auto":      None,
}

GEMINI_ASPECT_RATIOS = [
    "1:1", "1:4", "1:8", "2:3", "3:2", "3:4", "4:1", "4:3", "4:5",
    "5:4", "8:1", "9:16", "16:9", "21:9",
]

GEMINI_RESOLUTIONS = ["512", "1K", "2K", "4K"]

GEMINI_MODELS = {
    "flash": "gemini-2.5-flash-image",
    "nb2":   "gemini-3.1-flash-image-preview",
    "pro":   "gemini-3-pro-image-preview",
    "auto":  "gemini-3-pro-image-preview",  # Pro is default (best quality, prompt fidelity, text)
}

# Quality maps to resolution + model. Pro can't do 512, so low always uses NB2.
# Medium and high use Pro, which is the better model for most use cases.
QUALITY_TO_GEMINI = {
    "low":    {"resolution": "512", "model": "nb2"},
    "medium": {"resolution": "1K",  "model": "pro"},
    "high":   {"resolution": "4K",  "model": "pro"},
}

QUALITY_OPTIONS = ["low", "medium", "high"]
FORMAT_OPTIONS = ["png", "jpeg", "webp"]
BACKGROUND_OPTIONS = ["auto", "opaque"]
MODERATION_OPTIONS = ["auto", "low"]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}

DEFAULT_LATEST_DIRS = [
    Path.home() / "Desktop",
    Path.home() / "Downloads",
]

SESSIONS_DIR_NAME = ".image-sessions"
LAST_SESSION_FILE = "_last_session.txt"

PRESETS = {
    "concept": {
        "size": "landscape",
        "quality": "low",
        "format": "png",
        "variants": 4,
        "default_providers": ["gpt", "gemini"],
        "description": "dual-provider lowres concepting: 2 GPT + 2 Gemini",
    },
    "hq": {
        "size": "landscape",
        "quality": "high",
        "format": "png",
        "variants": 1,
        "default_providers": None,
        "description": "single hi-quality asset, kies provider met --gpt of --gemini",
    },
    "web": {
        "size": "landscape",
        "quality": "medium",
        "format": "webp",
        "variants": 2,
        "default_providers": None,
        "description": "medium quality, web asset",
    },
    "social": {
        "size": "portrait",
        "quality": "medium",
        "format": "png",
        "variants": 4,
        "default_providers": None,
        "description": "portrait social media asset",
    },
}


# ============================================================================
# HELPERS
# ============================================================================

def slugify(text, max_len=40):
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[\s_-]+', '-', text).strip('-')
    return text[:max_len] or "image"


def find_latest_image(directories):
    candidates = []
    for d in directories:
        if not d.is_dir():
            continue
        for f in d.iterdir():
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS:
                candidates.append(f)
    if not candidates:
        searched = ", ".join(str(d) for d in directories)
        sys.exit(f"No image files found in: {searched}")
    return max(candidates, key=lambda p: p.stat().st_mtime)


def save_image_bytes(image_bytes, base_prompt, provider, output_format, index=None, session_name=None):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    slug = slugify(base_prompt)
    suffix = f"_v{index}" if index is not None else ""
    session_tag = f"_{session_name}" if session_name else ""
    filename = f"{timestamp}_{slug}_{provider}{session_tag}{suffix}.{output_format}"
    path = Path.cwd() / filename
    if isinstance(image_bytes, str):
        image_bytes = base64.b64decode(image_bytes)
    path.write_bytes(image_bytes)
    return path


def save_sidecar(image_path, prompt, settings):
    txt_path = image_path.with_suffix('.txt')
    lines = [
        "Prompt:",
        prompt,
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Settings:",
    ]
    for k, v in settings.items():
        lines.append(f"  {k}: {v}")
    txt_path.write_text("\n".join(lines))


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

def sessions_dir():
    d = Path.cwd() / SESSIONS_DIR_NAME
    d.mkdir(exist_ok=True)
    return d


def session_path(name):
    return sessions_dir() / f"{name}.json"


def load_session(name):
    p = session_path(name)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text())
    except json.JSONDecodeError:
        sys.exit(f"Session file corrupt: {p}. Use --reset-session {name} to remove it.")


def save_session(name, state):
    p = session_path(name)
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2, default=str))
    tmp.replace(p)
    (sessions_dir() / LAST_SESSION_FILE).write_text(name)


def get_last_session_name():
    f = sessions_dir() / LAST_SESSION_FILE
    if not f.is_file():
        return None
    return f.read_text().strip() or None


def reset_session(name):
    p = session_path(name)
    if p.is_file():
        p.unlink()
        print(f"Removed session: {name}")
    else:
        print(f"No session found with name: {name}")
    last = sessions_dir() / LAST_SESSION_FILE
    if last.is_file() and last.read_text().strip() == name:
        last.unlink()


def list_sessions():
    d = sessions_dir()
    sessions = sorted(p.stem for p in d.glob("*.json"))
    if not sessions:
        print(f"No sessions in {d}")
        return
    last = get_last_session_name()
    print(f"Sessions in {d}:")
    for s in sessions:
        marker = "  <-- last used" if s == last else ""
        print(f"  {s}{marker}")


# ============================================================================
# OPENAI PROVIDER
# ============================================================================

def get_openai_client():
    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("Missing dependency. Run: pip3 install openai")
    key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
    if not key:
        sys.exit("No OpenAI API key. Paste into OPENAI_API_KEY at top of script, or set env var.")
    return OpenAI(api_key=key)


def gpt_generate_one(args, prompt, count, input_images):
    """Run ONE OpenAI call with given prompt and count. Returns list of (bytes, format)."""
    client = get_openai_client()
    actual_size = SIZE_TO_GPT.get(args.size, args.size)

    kwargs = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "size": actual_size,
        "quality": args.quality,
        "n": count,
    }
    if args.background and args.background != "auto":
        kwargs["background"] = args.background
    if args.moderation and args.moderation != "auto":
        kwargs["moderation"] = args.moderation
    if args.compression is not None and args.format in ("jpeg", "webp"):
        kwargs["output_compression"] = args.compression

    if input_images:
        if len(input_images) == 1:
            kwargs["image"] = open(input_images[0], "rb")
        else:
            kwargs["image"] = [open(p, "rb") for p in input_images]
        if args.mask:
            kwargs["mask"] = open(args.mask, "rb")
        response = client.images.edit(**kwargs)
    else:
        kwargs["output_format"] = args.format
        response = client.images.generate(**kwargs)

    return [(item.b64_json, args.format) for item in response.data]


def gpt_generate(args, jobs, input_images):
    """Run multiple OpenAI calls in parallel. jobs = list of (prompt, count) tuples."""
    if len(jobs) == 1:
        prompt, count = jobs[0]
        return gpt_generate_one(args, prompt, count, input_images)

    all_results = []
    with ThreadPoolExecutor(max_workers=len(jobs)) as executor:
        futures = [executor.submit(gpt_generate_one, args, p, c, input_images) for p, c in jobs]
        for f in as_completed(futures):
            all_results.extend(f.result())
    return all_results


# ============================================================================
# GEMINI PROVIDER
# ============================================================================

def get_gemini_client():
    try:
        from google import genai
    except ImportError:
        sys.exit("Missing dependency. Run: pip3 install google-genai")
    key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
    if not key:
        sys.exit("No Gemini API key. Paste into GEMINI_API_KEY at top of script, or set env var.")
    return genai.Client(api_key=key)


def resolve_gemini_settings(args):
    if args.aspect_ratio:
        aspect = args.aspect_ratio
    else:
        aspect = SIZE_TO_GEMINI_ASPECT.get(args.size)

    if args.resolution:
        resolution = args.resolution
    else:
        resolution = QUALITY_TO_GEMINI[args.quality]["resolution"]

    if args.gemini_model:
        model_tier = args.gemini_model
    else:
        model_tier = QUALITY_TO_GEMINI[args.quality]["model"]

    # --text modifier forces Pro
    if args.text:
        model_tier = "pro"
        # Pro doesn't support 512, bump to 1K
        if resolution == "512":
            print(f"  Note: --text forces Pro which doesn't support 512px, using 1K instead")
            resolution = "1K"

    # Pro doesn't support extreme aspect ratios
    if model_tier == "pro" and aspect in ("1:4", "1:8", "4:1", "8:1"):
        print(f"  Note: aspect {aspect} not supported by Gemini Pro, falling back to 16:9")
        aspect = "16:9"

    # 512 only on NB2
    if resolution == "512" and model_tier != "nb2":
        print(f"  Note: 512 resolution only on NB2, switching model")
        model_tier = "nb2"

    return {
        "model": GEMINI_MODELS[model_tier],
        "model_tier": model_tier,
        "aspect_ratio": aspect,
        "resolution": resolution,
    }


def build_gemini_config(settings, args):
    from google.genai import types
    config_kwargs = {"response_modalities": ["IMAGE"]}
    image_config = {}
    if settings["aspect_ratio"]:
        image_config["aspect_ratio"] = settings["aspect_ratio"]
    if settings["resolution"] and settings["model_tier"] != "flash":
        image_config["image_size"] = settings["resolution"]
    if image_config:
        config_kwargs["image_config"] = types.ImageConfig(**image_config)
    if args.grounding:
        config_kwargs["tools"] = [types.Tool(google_search=types.GoogleSearch())]
    return types.GenerateContentConfig(**config_kwargs)


def build_gemini_contents(prompt, input_images):
    from PIL import Image as PILImage
    contents = [prompt]
    if input_images:
        for img_path in input_images:
            contents.append(PILImage.open(img_path))
    return contents


def gemini_generate_one_stateless(args, settings, prompt, input_images):
    client = get_gemini_client()
    config = build_gemini_config(settings, args)
    contents = build_gemini_contents(prompt, input_images)
    response = client.models.generate_content(
        model=settings["model"],
        contents=contents,
        config=config,
    )
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
            return (part.inline_data.data, "png")
    raise RuntimeError("Gemini returned no image data")


def gemini_generate_session(args, settings, session_state, prompt, input_images):
    from google.genai import types
    client = get_gemini_client()
    config = build_gemini_config(settings, args)

    history = None
    if session_state.get("chat_history"):
        history = [types.Content.model_validate(c) for c in session_state["chat_history"]]

    chat = client.chats.create(
        model=settings["model"],
        config=config,
        history=history or [],
    )

    contents = build_gemini_contents(prompt, input_images)
    response = chat.send_message(contents)

    new_history = chat.get_history()
    session_state["chat_history"] = [c.model_dump(mode="json") for c in new_history]

    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data and part.inline_data.data:
            return (part.inline_data.data, "png")
    raise RuntimeError("Gemini session returned no image data")


def gemini_generate(args, jobs, input_images, session_state):
    """jobs = list of (prompt, count) tuples. For Gemini, count > 1 means same prompt repeated."""
    settings = resolve_gemini_settings(args)

    if session_state is not None:
        # Sessions are sequential, one call only
        prompt, _ = jobs[0]
        return [gemini_generate_session(args, settings, session_state, prompt, input_images)]

    # Expand jobs into a flat list of (prompt) calls
    calls = []
    for prompt, count in jobs:
        for _ in range(count):
            calls.append(prompt)

    if len(calls) == 1:
        return [gemini_generate_one_stateless(args, settings, calls[0], input_images)]

    results = []
    with ThreadPoolExecutor(max_workers=min(len(calls), 8)) as executor:
        futures = [
            executor.submit(gemini_generate_one_stateless, args, settings, p, input_images)
            for p in calls
        ]
        for f in as_completed(futures):
            results.append(f.result())
    return results


# ============================================================================
# ORCHESTRATION
# ============================================================================

def apply_preset(args, preset_name):
    preset = PRESETS[preset_name]
    args.size = args.size or preset["size"]
    args.quality = args.quality or preset["quality"]
    args.format = args.format or preset["format"]
    args.variants = args.variants or preset["variants"]
    return args


def apply_defaults(args):
    args.size = args.size or "square"
    args.quality = args.quality or "medium"
    args.format = args.format or "png"
    args.variants = args.variants or 1
    return args


def decide_providers(args):
    if args.gpt:
        return ["gpt"]
    if args.gemini:
        return ["gemini"]
    if args.preset:
        defaults = PRESETS[args.preset].get("default_providers")
        if defaults:
            return list(defaults)
    return ["gpt"]


def build_jobs_per_provider(variant_prompts, total_variants, providers):
    """
    Returns {provider: [(prompt, count), ...]}.

    Rules:
    - Single prompt (len 1): traditional n=count mode. Split count over providers.
    - Multiple prompts (len > 1): one call per prompt. Distribute alternating.
    """
    jobs = {p: [] for p in providers}
    dual = len(providers) == 2

    if len(variant_prompts) == 1:
        # Traditional: split count
        prompt = variant_prompts[0]
        if dual:
            half = total_variants // 2
            extra = total_variants - 2 * half  # 0 or 1
            gpt_count = half + extra
            gemini_count = half
            if gpt_count > 0:
                jobs["gpt"].append((prompt, gpt_count))
            if gemini_count > 0:
                jobs["gemini"].append((prompt, gemini_count))
        else:
            jobs[providers[0]].append((prompt, total_variants))
    else:
        # Multiple unique prompts: one call each
        if dual:
            for i, p in enumerate(variant_prompts):
                provider = "gpt" if i % 2 == 0 else "gemini"
                jobs[provider].append((p, 1))
        else:
            provider = providers[0]
            for p in variant_prompts:
                jobs[provider].append((p, 1))

    return jobs


def collect_input_images(args):
    images = []
    if args.edit:
        images.append(args.edit)
    if args.reference:
        images.extend(args.reference)
    return images


def run_provider(provider, args, jobs, input_images, session_state):
    if provider == "gpt":
        # GPT has no native chat session; prepend session's last image as input
        if session_state is not None:
            last = session_state.get("last_image_path")
            if last and Path(last).is_file():
                input_images = [last] + list(input_images or [])
        return gpt_generate(args, jobs, input_images=input_images if input_images else None)
    elif provider == "gemini":
        return gemini_generate(args, jobs,
                               input_images=input_images if input_images else None,
                               session_state=session_state)
    raise ValueError(f"Unknown provider: {provider}")


def main():
    parser = argparse.ArgumentParser(
        description="Dual-provider image generator: OpenAI GPT-Image-2 + Google Gemini Nano Banana",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("--reset-session", metavar="NAME",
                        help="Delete a stored session and exit")
    parser.add_argument("--list-sessions", action="store_true",
                        help="List all sessions in current folder and exit")

    parser.add_argument("prompt", nargs="?", help="Text prompt (or use --prompts for multiple)")

    # Presets
    preset_group = parser.add_mutually_exclusive_group()
    for name, cfg in PRESETS.items():
        preset_group.add_argument(
            f"--{name}",
            action="store_const", const=name, dest="preset",
            help=f"Preset: {cfg['description']}",
        )

    # Modifiers (NOT mutex with presets)
    parser.add_argument("--text", action="store_true",
                        help="Force Gemini Pro (best text rendering); compatible with all presets")

    # Provider
    provider_group = parser.add_mutually_exclusive_group()
    provider_group.add_argument("--gpt", action="store_true", help="OpenAI only")
    provider_group.add_argument("--gemini", action="store_true", help="Google Gemini only")

    # Generic
    parser.add_argument("--size", choices=list(SIZE_TO_GPT.keys()))
    parser.add_argument("--aspect-ratio", choices=GEMINI_ASPECT_RATIOS)
    parser.add_argument("--quality", choices=QUALITY_OPTIONS)
    parser.add_argument("--resolution", choices=GEMINI_RESOLUTIONS)
    parser.add_argument("--variants", "-n", type=int)
    parser.add_argument("--format", choices=FORMAT_OPTIONS)

    # Diverse variants
    parser.add_argument("--prompts", metavar="P1|P2|...",
                        help="Pipe-separated unique prompts for diverse concepts")

    # Gemini-specific
    parser.add_argument("--gemini-model", choices=list(GEMINI_MODELS.keys()))
    parser.add_argument("--grounding", action="store_true")

    # GPT-specific
    parser.add_argument("--background", choices=BACKGROUND_OPTIONS)
    parser.add_argument("--moderation", choices=MODERATION_OPTIONS)
    parser.add_argument("--compression", type=int, metavar="0-100")

    # Reference / edit
    parser.add_argument("--edit", metavar="IMAGE")
    parser.add_argument("--edit-latest", nargs="?", const="__DEFAULT__", metavar="DIR")
    parser.add_argument("--reference", "--ref", action="append", metavar="IMAGE")
    parser.add_argument("--mask", metavar="MASK")

    # Sessions
    parser.add_argument("--session", metavar="NAME")
    parser.add_argument("--continue", dest="continue_", action="store_true")

    # Workflow
    parser.add_argument("--skipquestions", action="store_true",
                        help="Geen vragen, defaults gebruiken")

    args = parser.parse_args()

    # Session subcommands
    if args.reset_session:
        reset_session(args.reset_session)
        return
    if args.list_sessions:
        list_sessions()
        return

    # Validate prompt source
    if not args.prompt and not args.prompts:
        parser.error("Need either a positional prompt or --prompts.")

    # Parse --prompts into a list
    if args.prompts:
        variant_prompts = [p.strip() for p in args.prompts.split('|') if p.strip()]
        if len(variant_prompts) < 1:
            sys.exit("--prompts must contain at least one prompt")
        # Override variants count to match
        args.variants = len(variant_prompts)
        # base_prompt for filename purposes
        base_prompt = variant_prompts[0]
    else:
        variant_prompts = [args.prompt]
        base_prompt = args.prompt

    # Validation
    if args.compression is not None and not (0 <= args.compression <= 100):
        sys.exit("--compression must be between 0 and 100")

    # Resolve --edit-latest
    if args.edit_latest:
        if args.edit:
            sys.exit("Cannot use both --edit and --edit-latest at the same time.")
        if args.edit_latest == "__DEFAULT__":
            search_dirs = DEFAULT_LATEST_DIRS
        else:
            search_dirs = [Path(args.edit_latest).expanduser()]
        latest = find_latest_image(search_dirs)
        print(f"Using latest image: {latest}")
        args.edit = str(latest)

    if args.edit and not Path(args.edit).is_file():
        sys.exit(f"Edit image not found: {args.edit}")
    if args.mask and not Path(args.mask).is_file():
        sys.exit(f"Mask image not found: {args.mask}")
    if args.reference:
        for r in args.reference:
            if not Path(r).is_file():
                sys.exit(f"Reference image not found: {r}")

    # Apply preset
    if args.preset:
        print(f"Preset: --{args.preset} ({PRESETS[args.preset]['description']})")
        args = apply_preset(args, args.preset)
        args.skipquestions = True

    if args.text:
        print("Modifier: --text (Gemini Pro forced)")

    args = apply_defaults(args)

    # Resolve session
    session_name = None
    session_state = None
    if args.continue_:
        if args.session:
            sys.exit("Use either --session NAME or --continue, not both.")
        session_name = get_last_session_name()
        if not session_name:
            sys.exit("No previous session in this folder. Start one with --session NAME.")
        session_state = load_session(session_name)
        if session_state is None:
            sys.exit(f"Last-used session '{session_name}' not found.")
        print(f"Continuing session: {session_name} (turn {session_state.get('turn_count', 0) + 1})")
    elif args.session:
        session_name = args.session
        session_state = load_session(session_name)
        if session_state is None:
            session_state = {
                "session_name": session_name,
                "provider": None,
                "created": datetime.now().isoformat(timespec="seconds"),
                "last_updated": None,
                "turn_count": 0,
                "last_image_path": None,
                "chat_history": [],
            }
            print(f"Starting new session: {session_name}")
        else:
            print(f"Resuming session: {session_name} (turn {session_state.get('turn_count', 0) + 1})")

    # Decide providers
    providers = decide_providers(args)

    # Sessions: single provider, single prompt only
    if session_state is not None:
        if len(providers) > 1:
            sys.exit("Sessions require a single provider. Use --gpt or --gemini.")
        if len(variant_prompts) > 1:
            sys.exit("Sessions can only handle one prompt per turn. Use --prompts only in stateless mode.")
        pinned = session_state.get("provider")
        if pinned and pinned != providers[0]:
            sys.exit(f"Session '{session_name}' is pinned to provider '{pinned}'. "
                     f"You requested '{providers[0]}'. Use --reset-session to start over.")
        session_state["provider"] = providers[0]

    # Edit/reference requires single provider
    input_images = collect_input_images(args)
    if input_images and len(providers) > 1:
        sys.exit("Edit/reference mode requires a single provider. Use --gpt or --gemini.")

    # Build per-provider jobs
    jobs = build_jobs_per_provider(variant_prompts, args.variants, providers)

    # Report plan
    print(f"\nPlan:")
    if len(variant_prompts) == 1:
        print(f"  prompt:     {variant_prompts[0]}")
    else:
        print(f"  prompts:    {len(variant_prompts)} unique")
        for i, p in enumerate(variant_prompts, 1):
            print(f"    {i}. {p}")
    print(f"  size:       {args.size}{' (aspect ' + args.aspect_ratio + ')' if args.aspect_ratio else ''}")
    print(f"  quality:    {args.quality}")
    if args.resolution:
        print(f"  resolution: {args.resolution} (Gemini)")
    print(f"  providers:  {', '.join(providers)}")
    for p, job_list in jobs.items():
        if job_list:
            calls_desc = ", ".join(f"{c}x" for _, c in job_list)
            print(f"    {p}: {len(job_list)} call(s), counts: {calls_desc}")
    if input_images:
        print(f"  input images: {len(input_images)}")
        for p in input_images:
            print(f"    - {p}")
    if session_name:
        print(f"  session:    {session_name}")
    if args.grounding:
        print(f"  grounding:  enabled")
    if args.text:
        print(f"  text mode:  Gemini Pro forced")

    # Run providers in parallel
    print(f"\nGenerating...")
    all_results = {}
    active_providers = [p for p in providers if jobs[p]]
    with ThreadPoolExecutor(max_workers=len(active_providers)) as executor:
        futures = {
            executor.submit(run_provider, p, args, jobs[p], input_images, session_state): p
            for p in active_providers
        }
        for future in as_completed(futures):
            provider = futures[future]
            try:
                all_results[provider] = future.result()
                print(f"  [OK] {provider}: {len(all_results[provider])} image(s)")
            except Exception as e:
                print(f"  [FAIL] {provider}: {e}")
                all_results[provider] = []

    # Settings dict for sidecar
    settings = {
        "mode": "edit" if input_images else "generate",
        "size": args.size,
        "quality": args.quality,
        "variants_total": args.variants,
        "providers": ", ".join(providers),
    }
    if args.aspect_ratio:
        settings["aspect_ratio"] = args.aspect_ratio
    if args.resolution:
        settings["resolution"] = args.resolution
    if args.gemini_model:
        settings["gemini_model"] = args.gemini_model
    if args.text:
        settings["text_mode"] = True
    if args.grounding:
        settings["grounding"] = True
    if args.preset:
        settings["preset"] = args.preset
    if input_images:
        settings["input_images"] = ", ".join(input_images)
    if session_name:
        settings["session"] = session_name
    if len(variant_prompts) > 1:
        settings["unique_prompts"] = len(variant_prompts)

    # Save outputs
    print(f"\nSaving to: {Path.cwd()}")
    total_saved = 0
    last_saved_path = None
    for provider, results in all_results.items():
        for i, (image_data, fmt) in enumerate(results, 1):
            idx = i if len(results) > 1 else None
            path = save_image_bytes(image_data, base_prompt, provider, fmt, idx, session_name)
            # Sidecar uses the unique prompt for this variant if multi-prompt, otherwise base
            sidecar_prompt = base_prompt
            save_sidecar(path, sidecar_prompt, settings)
            print(f"  [{provider}] {path.name}")
            total_saved += 1
            last_saved_path = path

    # Persist session
    if session_state is not None and last_saved_path:
        session_state["last_image_path"] = str(last_saved_path)
        session_state["turn_count"] = session_state.get("turn_count", 0) + 1
        session_state["last_updated"] = datetime.now().isoformat(timespec="seconds")
        save_session(session_name, session_state)
        print(f"\nSession '{session_name}' saved (turn {session_state['turn_count']}).")

    print(f"\nDone. {total_saved} image(s) saved.")


if __name__ == "__main__":
    main()
