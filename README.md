# Image Skill — Dual-Provider Image Generator

One Claude Code skill, two image providers: **OpenAI GPT-Image-2** and
**Google Gemini Nano Banana (Pro)**. Claude picks the right provider and
mode based on the briefing — the skill provides the building blocks,
Claude orchestrates.

> Designed as a drop-in skill for Claude Code / claude.ai. Also works as
> a standalone CLI script.

---

## ⚠️ Read this about API keys first

This script talks to paid APIs (OpenAI + Google Gemini). The keys are
**not** included in this repo.

- **`generate.py`** = the working script, with your keys. Listed in
  [.gitignore](.gitignore) and **never** committed.
- **`generate.example.py`** = the exact same script, but with empty keys.
  This is what you see in the repo.

During installation you copy the template to `generate.py` and put your
keys there. That way a key can never accidentally end up on GitHub.

Why keys go *in the file* (and not only as environment variables): the
skill also runs through **claude.ai / Claude desktop**, where no shell
environment variables are available. The script supports both: a key
filled in inside the file, or the env vars `OPENAI_API_KEY` /
`GEMINI_API_KEY` (the env var is used when the in-file key is empty).

---

## Requirements

- Python 3.9+
- An **OpenAI API key** with GPT-Image-2 access — create one at
  [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
- A **Google Gemini API key** with Nano Banana / NB2 / Pro access — create one at
  [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- Python packages: `openai`, `google-genai`, `pillow` (the installer handles this)

---

## Automated installation (recommended)

The automated route does everything for you: installs dependencies, asks
for your keys safely, places the skill in `~/.claude/skills/image/` (for
Claude Code) and builds an `image.skill` bundle (for import into
claude.ai / Claude desktop). You don't need to copy, rename, or look up
line numbers.

Pick one of the two routes below — both lead to the same result.

### Route A — macOS double-click (no terminal needed)

Got this repo as a ZIP? Unzip it and **double-click `install.command`**
in Finder. Terminal opens automatically and runs the installer.

> **First time:** macOS Gatekeeper may say *"cannot be opened because
> it is from an unidentified developer"*. **Right-click** on
> `install.command` → **Open** → **Open**. You only need to do this once.
>
> **Double-click doesn't work?** Open Terminal, drag `install.command`
> into it, press Enter.

### Route B — Terminal (all platforms)

```bash
git clone https://github.com/mischacoster/image-skill.git
cd image-skill
./setup.py
```

### What the installer does

Both routes run `setup.py` and walk through these steps:

1. **Dependencies** — installs `openai`, `google-genai`, `pillow` via pip
2. **Keys** — asks for your OpenAI and Gemini key (hidden input, not in shell history)
3. **Local install** — writes `~/.claude/skills/image/{SKILL.md, generate.py}` with mode `600` (Claude Code picks it up automatically)
4. **Bundle** — builds `image.skill` in the current directory (mode `600`) for import into claude.ai / desktop

### Useful flags

```bash
./setup.py --no-deps          # skip pip install (if deps are already there)
./setup.py --no-local         # bundle only, no local install
./setup.py --no-bundle        # local install only, no bundle
./setup.py --bundle-path ~/Desktop/image.skill
./setup.py --yes              # accept all prompts
./setup.py --help
```

> **⚠ Security — `image.skill` contains your API keys.**
> Treat it like a password: don't commit it, don't put it in
> iCloud/Dropbox, don't share it without reason. Anyone with this file
> can run paid API calls on your account. The script writes mode `600`
> so only you can read it.

### Importing into claude.ai or Claude desktop

1. Open *Settings → Skills* (or *Capabilities → Skills*).
2. Choose *Create skill* / *Upload* and select `image.skill`.
3. First call in a new session: the sandbox automatically installs the
   Python deps (~10–20s overhead). After that it runs at normal speed.

---

## Manual installation

> Only needed if you don't want to use the setup script. The automated
> route above does everything that is done manually here — pick one or
> the other, not both.

```bash
git clone https://github.com/mischacoster/image-skill.git ~/.claude/skills/image
cd ~/.claude/skills/image
pip3 install openai google-genai pillow
cp generate.example.py generate.py
```

Open `generate.py` and fill in your keys at the top (lines 75–76):

```python
OPENAI_API_KEY = "sk-proj-..."   # your OpenAI key
GEMINI_API_KEY = "AIza..."       # your Gemini key
```

Or leave them empty and use environment variables instead (only works in
local Claude Code — not in claude.ai/desktop, where the key *must* be in
the file):

```bash
export OPENAI_API_KEY="sk-proj-..."
export GEMINI_API_KEY="AIza..."
```

Standalone use works too:

```bash
python3 ~/.claude/skills/image/generate.py "a minimalist brain logo" --hq --gpt
```

---

## Quick usage

Claude detects what you need and picks provider + mode. You can also
steer explicitly with the switches below.

| Mode | Trigger | What it does |
|---|---|---|
| **Concept** (`--concept`) | "explore", "ideas", "variants", vague briefing | 4 diverse concepts, dual (2 GPT + 2 Gemini), fast/low-res |
| **HQ** (`--hq`) | explicit "final", "for production", "in HQ", "in hires" | 1 hi-res asset — Claude only triggers HQ when you ask for it |
| **Web** (`--web`) | web asset | 2 variants, medium |
| **Social** (`--social`) | social media | 4 variants, medium |
| **Text** (`--text`) | infographic, labels, headline in image | modifier, forces Gemini Pro (combines with any preset) |
| **Reference** (`--reference IMG`) | "place this product in…", "this person in scene" | generates based on 1+ reference images |
| **Edit** (`--edit IMG`) | modify an existing image | edits a provided image |
| **Session** (`--session NAME` / `--continue`) | "build on…", iterations | multi-turn, preserves context across calls |
| **Analyze** (`--analyze IMG`) | "describe this", "what style is this", save a look | image → structured JSON (subject, style, composition, palette, lighting, mood). Pair with `--save-style NAME` to save as reusable fingerprint. |
| **Style fingerprint** (`--style NAME`) | "generate in the style of brand-look" | injects a saved style preamble into the prompt before generation |

> **Cost discipline:** the skill defaults to **medium quality** for iteration.
> Only `--concept` (low) and explicit `--hq` (high) deviate. Reference, edit,
> merge and session calls stay at medium until you ask for the final HQ version.

---

## Choosing a provider

Default for `--concept`: dual mode (2 GPT + 2 Gemini). For everything
else:

| Briefing signal | Provider | Reason |
|---|---|---|
| Infographic, poster with text, UI mockup | **GPT** | Text rendering, spatial logic, instruction-following |
| Hyperrealistic portrait, product photography | **Gemini Pro** | Natural skin, "real camera" |
| Style transfer (pop-art, watercolor, vintage) | **Gemini Pro** | Stronger style transfer |
| Cinematic atmosphere, mood, lighting (no text) | **Gemini Pro** | Atmosphere and lighting |
| Strict brand rules (exact color/font) | **GPT** | Higher on instruction-following |
| Combining photos into one scene | **Gemini Pro** | Mature multi-image fusion |
| Edit existing photo, remove people | **GPT** | Stable iterative edits |
| Recognizable real person in scene | **GPT** | Face fidelity / identity preservation |
| Public figure (politician, CEO) | **GPT** | Gemini often blocks with policy message |
| Speed + many iterations | **GPT** | ~3 sec vs 10–15 sec |
| Non-Latin text (Kanji, Cyrillic, Arabic) | **GPT** | Multilingual text fidelity |
| Editorial layout, complex grid | **GPT** | Layout knowledge stronger |

---

## All switches

**Presets** (pick max 1): `--concept` · `--hq` · `--web` · `--social`

**Modifier** (combinable): `--text` (forces Gemini Pro)

**Provider** (pick max 1): `--gpt` · `--gemini`

**Generic:**
- `--size square|landscape|portrait|auto`
- `--aspect-ratio` (Gemini-specific)
- `--quality low|medium|high`
- `--variants N` / `-n N`
- `--format png|jpeg|webp` (GPT)

**Diverse prompts:** `--prompts "p1|p2|p3|p4"` (4 genuinely different prompts)

**Gemini:** `--resolution 512|1K|2K|4K` · `--gemini-model flash|nb2|pro|auto` · `--grounding`

**GPT:** `--background auto|opaque|transparent` · `--nobg` (shortcut for transparent → auto-routes to gpt-image-1.5) · `--gpt-1K` / `--gpt-2K` (native 2K on gpt-image-2; 1K is default) · `--moderation auto|low` · `--compression 0-100`

> **Batch consistency:** GPT with `--variants N` (max 8) on a single prompt returns a character-consistent set on gpt-image-2.

**Reference / edit** (single-provider): `--reference IMG` (multiple allowed) · `--edit IMG` · `--edit-latest [DIR]` · `--mask IMG`

**Sessions** (single-provider): `--session NAME` · `--continue` · `--reset-session NAME` · `--list-sessions`

**Analyze + style library** (single-provider, Gemini): `--analyze IMG` · `--save-style NAME` (save analyzed JSON to library) · `--style NAME` (inject saved style into prompt) · `--list-styles`

**Cost tracking:** `--costs` · `--days N` (restrict to last N days)

**Workflow:** `--skipquestions`

### Quality mapping (Gemini)

| Quality | Resolution | Model | Note |
|---|---|---|---|
| low | 512 | NB2 | Pro can't do 512 |
| medium | 1K | Pro | Default Pro |
| high | 4K | Pro | Default Pro |

With `--text`, low automatically becomes 1K + Pro.

---

## Examples

```bash
# Dual concept with diverse prompts
python3 ~/.claude/skills/image/generate.py "illustration for a Status Quo Bias column" \
  --concept --prompts "editorial vector, person frozen at fork in road|metaphorical photorealistic, anchor pulling someone down|3D isometric comfort zone|abstract minimalist with weights"

# Iterating in medium (default) — product in a new setting
python3 ~/.claude/skills/image/generate.py "place this bottle on a natural stone counter, morning light" --reference bottle.jpg --gemini

# Recognizable person in scene (GPT for face fidelity) — still medium during iteration
python3 ~/.claude/skills/image/generate.py "this person as a speaker at a TEDx stage" --reference photo.jpg --gpt

# Iterative session — medium throughout
python3 ~/.claude/skills/image/generate.py "futuristic dashboard, dark mode" --session dash --gemini
python3 ~/.claude/skills/image/generate.py "add a chart on the right" --continue
python3 ~/.claude/skills/image/generate.py "warmer color palette" --continue

# Only when you ask for the final version: HQ
python3 ~/.claude/skills/image/generate.py "minimalist logo, geometric brain icon" --hq --gpt
python3 ~/.claude/skills/image/generate.py "infographic about confirmation bias with labels and title" --text --gpt --hq

# Transparent PNG logo — auto-routes to gpt-image-1.5
python3 ~/.claude/skills/image/generate.py "minimalist geometric brain icon, vector style" --gpt --nobg --hq

# Native 2K on gpt-image-2 (only on --hq, never auto)
python3 ~/.claude/skills/image/generate.py "editorial illustration about decision fatigue" --gpt --hq --gpt-2K

# Character-consistent set of 6 variants in one batch (medium iteration)
python3 ~/.claude/skills/image/generate.py "founder portrait, four-point lighting, neutral grey backdrop" --gpt --variants 6

# Analyze an image + save its style as a reusable fingerprint
python3 ~/.claude/skills/image/generate.py --analyze reference.jpg --save-style brand-look

# Generate a new subject in that saved style
python3 ~/.claude/skills/image/generate.py "a workspace scene" --style brand-look --gemini

# Show what this project has cost so far
python3 ~/.claude/skills/image/generate.py --costs
python3 ~/.claude/skills/image/generate.py --costs --days 1
```

---

## Output

Files land in the current working directory:

- `2026-05-16_141523_your-prompt-slug_gpt_v1.png`
- `2026-05-16_141523_your-prompt-slug_gemini_v1.png`
- `2026-05-16_141523_your-prompt-slug_gemini_dash.png` (session-tagged)
- A `.txt` sidecar per image with the prompt + settings used

Session state lives per project folder in `./.image-sessions/{name}.json`.
Cost log per project: `./.image-sessions/costs.json`.
Style library (user-global, reusable across projects):
`~/.claude/skills/image/.styles/{name}.json`.

> Generated images, sidecars and session state are listed in
> [.gitignore](.gitignore) and are deliberately not committed.

---

## Provider properties

| Property | GPT-Image-2 | Gemini Nano Banana |
|---|---|---|
| Best for | Text, layout, identity preservation, iterative edits | Photorealism, atmosphere, style transfer, multi-reference |
| Text in image | Excellent (incl. non-Latin) | Good, less dense |
| Public figures | Allowed | Often blocked |
| Speed | ~3 sec | 10–15 sec |
| Max resolution | 2K native (gpt-image-2 via `--gpt-2K`); 1024×1536 default | 4K (NB2 and Pro) |
| Native chat sessions | No (edit-chain) | Yes (thought signatures) |
| Reference images | Yes (image.edit) | Yes (up to 14 for Pro) |
| Edit with mask | Yes | No (semantic inpainting via prompt) |
| Grounding on real-time data | No | Yes (Google Search) |
| Watermark | No | SynthID (invisible) |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `No OpenAI API key` / `No Gemini API key` | Key not filled in `generate.py` and no env var set. Do one of the two. |
| `ModuleNotFoundError: openai` | `pip3 install openai google-genai pillow` |
| Claude doesn't see the skill | Repo must live in `~/.claude/skills/image/` and contain `SKILL.md` |
| Gemini refuses a known person | Use `--gpt` (Gemini blocks public figures) |
| `generate.py` shows up in `git status` | That shouldn't happen — check that [.gitignore](.gitignore) contains the line `generate.py` |

---

## Files in this repo

| File | Role |
|---|---|
| `SKILL.md` | Skill instructions for Claude (decision flow, cost discipline, quick reference) |
| `references/` | Progressive-disclosure detail files loaded by Claude on demand (provider matrix, concept mode, modes & examples) |
| `generate.example.py` | The script without keys — copy to `generate.py` |
| `generate.py` | Your working script with keys — **not** in git (`.gitignore`) |
| `setup.py` | Setup script: deps, keys, local install + bundle build |
| `install.command` | macOS double-click launcher for `setup.py` (non-tech) |
| `image.skill` | Generated bundle with keys — **not** in git (`.gitignore`) |
| `README.md` | This file |
| `LICENSE` | MIT license |
| `.gitignore` | Keeps keys, output, bundle and session state out of git |

---

## License

MIT — see [LICENSE](LICENSE). Fork, adapt and share freely; attribution
appreciated but not required.
