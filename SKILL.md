---
name: image
description: Dual-provider image generator (OpenAI GPT-Image-2 + Google Gemini Nano Banana). Use this skill for all image creation unless the user explicitly invokes a different skill or MCP. Detect whether the user is exploring conceptually (--concept, dual, ALWAYS with diverse prompts), wants a final asset (--hq), text-rich content (--text), wants to place a product in a setting (--reference), or is iterating on a previous result (--session). When the user attaches images: automatically use edit mode.
tools:
  - Bash
  - Read
---

# Dual-Provider Image Generator (GPT-Image-2 + Gemini Nano Banana)

One skill, two providers, one Claude that picks based on the briefing. The skill provides the building blocks; Claude orchestrates the combination. Default mindset: ask as few questions as possible, but make the right choices.

## Decision flow

### 1. First check: do I have enough to start?

If the user types only "image" without further context: ask in natural language about the subject and a style direction. For example:

> "What should the image be about? Do you have a style direction in mind, for example photorealistic, editorial illustration, minimalist, 3D, cartoon, or something else?"

Wait for an answer before continuing.

If the user provides a subject but no style AND there is no reference image: ask the style question through `ask_user_input_v0` (or a natural question) before generating four concepts. Reason: with `--concept` you would otherwise produce four different styles, but if the user already has a style in mind, three of them are automatically off the table. Better to check first.

When a style is mentioned in the briefing (for example "editorial vector illustration" or "photorealistic portrait") or there is a reference image that implies the style: continue directly without asking.

### 2. Detect the type

Concept mode (`--concept`) for briefings with:
- "concept", "concepts", "ideas", "explore", "brainstorm"
- "variants", "find direction", "what fits"
- "show me something"
- vague or broad descriptions

HQ mode (`--hq`) for briefings with:
- "final", "definitive", "for production", "for publication"
- "high quality", "sharp", "print"

Text modifier (`--text`) for briefings that mention:
- "infographic", "diagram", "schema with labels"
- "headline X", "title Y", "text Z in image"
- "column illustration with heading"

Reference mode (`--reference`):
- "place this product in..."
- "use this [logo/photo/character] in a new scene"
- "in the same style as..."

Edit mode (`--edit`) when the user attaches an image with an edit request.

Session mode (`--session`/`--continue`):
- "build on...", "continue with...", "now also add X"
- follow-up questions to a previous generation

### 3. Choose a provider based on the use case

Default for `--concept` without further indication: dual mode (2 GPT + 2 Gemini). For other modes: use the matrix below.

| Briefing signal | Provider | Reason |
|---|---|---|
| Infographic, poster with text elements, UI mockup | **GPT** | Text rendering, spatial logic, instruction-following |
| Hyperrealistic portrait, skin texture, product photography | **Gemini Pro** | Subsurface scattering, natural skin, "real camera" |
| Style transfer (pop-art, watercolor, dramatic b/w, vintage) | **Gemini Pro** | Style transfer is stronger, less "plastic AI look" |
| Cinematic atmosphere, mood, lighting (no text) | **Gemini Pro** | Atmosphere and lighting |
| Logo upload → product icons (brand visual system) | **Gemini Pro** | Up to 14 references for consistency |
| Strict brand-rule adherence (exact color, exact font) | **GPT** | Higher on instruction-following |
| Combining photos into one scene (multi-image fusion) | **Gemini Pro** | Mature multi-image fusion |
| Editing an existing photo, removing people, changing a scene | **GPT** | Stable iterative edits + face fidelity |
| Recognizable real person (yourself, family, clients) in scene | **GPT** | Face fidelity, identity preservation |
| Public figure (politician, CEO, etc.) | **GPT** | Gemini often blocks with a policy message |
| Speed priority, many iterations | **GPT** | 3 sec vs 10-15 sec |
| Non-Latin text (Kanji, Cyrillic, Arabic) | **GPT** | Multilingual text fidelity higher |
| Editorial layout, complex grid, magazine style | **GPT** | Layout knowledge stronger |

When in doubt between two: ask the user, or run both via dual mode (only possible without a reference image).

### 4. Additional questions (max 2 per turn)

Only ask questions that actually change the result. Two is the maximum.

Do ask:
- Style direction if there is no reference image and no style in the briefing
- Orientation/aspect ratio if the briefing doesn't mention shape and the context is unclear
- Provider choice if the briefing balances between GPT and Gemini strengths

Don't ask:
- For `--concept` with a clear style direction or a reference: just run
- Format, background, compression: use defaults unless specifically relevant
- Number of variants: default 4 for concept, 1 for hq

### 5. With `--concept`: tune the variation strategy to the briefing

Important fix for "4 concepts that are actually 2 ideas": always use `--prompts` with four genuinely different prompts. But choose the variation axis carefully:

**If the user did not mention a style direction** (and you either asked or didn't): vary along the style axis (editorial vector / photorealistic / 3D isometric / minimalist metaphor).

**If a style was mentioned** ("editorial illustration", "photorealistic", "minimalist"): keep the style constant across all 4 and vary along other axes:
- Composition/perspective (close-up, wide, isometric, dynamic angle)
- Interpretation (literal, metaphorical, abstract, symbolic)
- Mood (serene, energetic, dramatic, contemplative)
- Color palette (within the given style)

**If a reference image was provided**: the style is largely determined by the reference. Vary along composition, perspective, and context (different settings in which the reference subject appears).

Variation axes to pick from (combine two at a time for maximum spread):
- Style: editorial vector / photorealism / 3D isometric / pencil sketch / vector flat / watercolor / technical diagram / claymation / low-poly
- Composition: close-up / wide shot / isometric / top-down / first person / dynamic asymmetric
- Interpretation: literal / metaphorical / abstract / symbolic / narrative scene
- Mood: serene / energetic / dramatic / playful / minimalist / dystopian
- Medium: digital / sketch / watercolor / 3D render / photography / collage
- Color palette: high-contrast / monochrome / vibrant / muted earth / two-tone / single accent

> Personal preferences (accessibility needs like color-blindness, preferred palettes, brands to avoid) belong in your global `CLAUDE.md`, not in this skill. The skill stays neutral so it works for everyone.

## Provider caveats (important to weigh)

**Public figures**: Gemini blocks prompts featuring recognizable famous people (politicians, CEOs, celebrities) with a policy message. GPT does them. Always use `--gpt` for these.

**Speed**: GPT-Image-2 takes ~3 seconds per call, Nano Banana Pro 10-15 seconds. In dual mode, wall time is determined by Gemini.

**Watermark**: Gemini outputs carry a SynthID watermark by default (invisible but detectable). GPT does not. Irrelevant for most use cases, but use GPT if forensic analysis matters or watermark interference is a problem.

**Editorial vs photorealistic trade-off**: GPT often delivers "polished, clean, slightly digital painting" output. Gemini often delivers "natural, less AI-polished, photographic" output. Choose based on what you need.

**4K**: Gemini supports native 4K from NB2 onward. GPT-Image-2 maxes out around 1536x1024.

## Concept → final with consistency

Pro is the default for medium and high quality. For low (concept) it stays NB2 because only NB2 can do 512px. Three strategies to keep consistency between concept and final:

**Option 1, concept as reference**:
```bash
# Concept (NB2 at 512)
python3 ~/.claude/skills/image/generate.py "logo for a creative studio" --concept --prompts "..."

# Final with the approved concept as reference (Pro at 4K)
python3 ~/.claude/skills/image/generate.py "produce hi-res production version, identical composition and style" --reference 2026-05-16_..._gemini_v2.png --gemini --quality high
```

**Option 2, session**:
```bash
python3 ~/.claude/skills/image/generate.py "logo for a creative studio" --session studio-logo --gemini --quality medium
python3 ~/.claude/skills/image/generate.py "now in 4K, exact same composition" --continue --quality high
```

**Option 3, stay on NB2**:
```bash
python3 ~/.claude/skills/image/generate.py "logo for a creative studio" --hq --gemini --gemini-model nb2 --resolution 4K
```

## Reference mode (product in setting, recognizable person)

For "place this in setting X" or "this person in this scene":

```bash
# Product in a new location
python3 ~/.claude/skills/image/generate.py "place this perfume bottle on a marble bathroom counter with soft natural light" --reference perfume.jpg --gemini --quality high

# Recognizable person in scene (GPT for face fidelity)
python3 ~/.claude/skills/image/generate.py "this person as an illusionist in a packed theater with a fireball" --reference photo.jpg --gpt --hq

# Multi-reference composition
python3 ~/.claude/skills/image/generate.py "place this logo on a white t-shirt, worn by this model" --reference logo.png --reference model.jpg --gemini --quality high
```

Provider choice with a reference image:
- Reference is a **recognizable real person** who must stay identical → **GPT** (face fidelity)
- Reference is a **product** that must go into a new scene → **Gemini** (composition stronger)
- Reference is a **logo or brand asset** → **Gemini** (multi-reference mature)
- Reference is a **fictional character** who must stay recognizable across scenes → **Gemini** (character continuity)

## Edit mode (modifying an existing image)

When the user attaches an image and asks for a change:
1. Detect the file path
2. Pass it through `--edit`
3. Force the provider based on what needs to happen:
   - Edit while preserving a recognizable person: `--gpt`
   - Style transfer or atmosphere change: `--gemini`
   - Removing people, scene composition changes, iterative edits: `--gpt`
4. `--skipquestions` to skip extra questions

```bash
python3 ~/.claude/skills/image/generate.py "remove the other people from the square so only this person remains" --edit /path/to/photo.jpg --gpt --skipquestions
```

## Multi-turn sessions (iterating over time)

```bash
# Start a session
python3 ~/.claude/skills/image/generate.py "futuristic dashboard, dark mode" --session dashboard-ui --gemini --quality medium

# Iterations within the session
python3 ~/.claude/skills/image/generate.py "add a chart on the right" --continue
python3 ~/.claude/skills/image/generate.py "warmer color palette" --continue

# Management
python3 ~/.claude/skills/image/generate.py --list-sessions
python3 ~/.claude/skills/image/generate.py --reset-session dashboard-ui
```

State is stored per project folder in `./.image-sessions/{name}.json`. For Gemini: real chat API with thought signatures. For GPT: edit-chain with the latest output as input.

## Behavior after generation

Speed of delivery over analysis. Show the files with the shortest possible confirmation:

- For `--concept`: "4 concepts ready, varied along [style/composition/etc]"
- For `--hq`: "Here is your hi-res asset"
- For sessions: "Turn 3 in [session name]"

No analysis, comparison, or suggestions unless asked. Always close with:

> *"Want me to analyze the images or develop a specific direction further?"*

Only when explicitly asked for analysis, critique, or prompt improvement, provide it in detail.

## First-time setup

```bash
pip3 install openai google-genai pillow
```

Open `generate.py` and paste your API keys at the top:
- `OPENAI_API_KEY = "sk-proj-..."`
- `GEMINI_API_KEY = "AIza..."`

## Presets and modifiers

| Name | Type | Default providers | Variants | Quality | Use case |
|---|---|---|---|---|---|
| `--concept` | preset | dual | 4 (2+2) | low | Explore quickly with diverse prompts |
| `--hq` | preset | choose explicitly | 1 | high | Final asset |
| `--web` | preset | choose explicitly | 2 | medium | Web asset |
| `--social` | preset | choose explicitly | 4 | medium | Social media |
| `--text` | modifier | (follows preset) | (follows preset) | (follows preset) | Force Gemini Pro |

`--text` is a modifier and combines with any preset. With `--concept --text` the Gemini side bumps from 512 to 1K (Pro cannot do 512).

## Quality mapping for Gemini

| Quality | Resolution | Model | Note |
|---|---|---|---|
| low | 512 | NB2 | Pro cannot do 512, so always NB2 |
| medium | 1K | Pro | Default Pro |
| high | 4K | Pro | Default Pro |

With `--text`: low becomes 1K + Pro, medium and high stay 1K/4K + Pro.

## Invocation examples

```bash
# Dual concept with diverse prompts (no style direction given)
python3 ~/.claude/skills/image/generate.py "an illustration for a Status Quo Bias column" --concept --prompts "editorial vector style, person frozen at fork in road|metaphorical photorealistic, anchor pulling someone down|3D isometric scene of comfort zone|abstract minimalist composition with weights"

# Dual concept with style direction given: vary on other axes
python3 ~/.claude/skills/image/generate.py "editorial vector illustration for a Confirmation Bias column" --concept --prompts "person looking through colored glasses at a book, close-up|cluttered desk with selective post-it markings, top-down|silhouettes against a wall of TVs showing same news, wide|two paths diverging with one brightly lit, isometric"

# Hi-quality final with GPT (strong instruction-following, brand assets)
python3 ~/.claude/skills/image/generate.py "minimalist logo for a creative studio, geometric brain icon" --hq --gpt

# Hi-quality photorealistic with Gemini Pro
python3 ~/.claude/skills/image/generate.py "modern lifestyle scene of someone working from home at the kitchen table, morning light" --hq --gemini

# Infographic with text (GPT for text rendering)
python3 ~/.claude/skills/image/generate.py "infographic about confirmation bias with clear labels and title" --text --gpt --hq

# Product in a new setting
python3 ~/.claude/skills/image/generate.py "place this bottle on a natural stone counter, morning light" --reference bottle.jpg --gemini --quality high

# Recognizable person in scene (GPT for face fidelity)
python3 ~/.claude/skills/image/generate.py "this person as a speaker at a TEDx stage, dark background with TEDx logo" --reference photo.jpg --gpt --hq

# Remove people from a photo (GPT for stable edits)
python3 ~/.claude/skills/image/generate.py "remove all other people around the central person, as if they are alone on the square" --edit photo.jpg --gpt --skipquestions

# Banner with aspect ratio
python3 ~/.claude/skills/image/generate.py "LinkedIn article banner about cognitive biases" --gemini --aspect-ratio 21:9 --quality high

# With grounding for real-time data
python3 ~/.claude/skills/image/generate.py "visualize current 12-month interest rate trend" --gemini --grounding --quality high

# Session for iteration
python3 ~/.claude/skills/image/generate.py "futuristic dashboard, dark mode" --session dash --gemini --quality medium
python3 ~/.claude/skills/image/generate.py "add a chart on the right" --continue
python3 ~/.claude/skills/image/generate.py "warmer color palette" --continue
```

## All switches

**Presets** (pick max 1): `--concept`, `--hq`, `--web`, `--social`

**Modifier** (combinable): `--text` (force Gemini Pro)

**Provider** (pick max 1): `--gpt`, `--gemini`

**Generic:**
- `--size square|landscape|portrait|auto`
- `--aspect-ratio` (Gemini-specific)
- `--quality low|medium|high`
- `--variants N` / `-n N`
- `--format png|jpeg|webp` (GPT)

**Diverse prompts:** `--prompts "p1|p2|p3|p4"`

**Gemini:** `--resolution 512|1K|2K|4K`, `--gemini-model flash|nb2|pro|auto`, `--grounding`

**GPT:** `--background auto|opaque`, `--moderation auto|low`, `--compression 0-100`

**Reference/edit (single-provider):** `--reference IMAGE` (multiple allowed), `--edit IMAGE`, `--edit-latest [DIR]`, `--mask IMAGE`

**Sessions (single-provider):** `--session NAME`, `--continue`, `--reset-session NAME`, `--list-sessions`

**Workflow:** `--skipquestions`

## Output

In the current working directory:
- `2026-05-16_141523_your-prompt-slug_gpt_v1.png`
- `2026-05-16_141523_your-prompt-slug_gemini_v1.png`
- `2026-05-16_141523_your-prompt-slug_gemini_dash.png` (session-tagged)
- `.txt` sidecar per image with prompt + settings

## Provider properties summary

| Property | GPT-Image-2 | Gemini Nano Banana |
|---|---|---|
| Best for | Text, layout, identity preservation, iterative edits | Photorealism, atmosphere, style transfer, multi-reference |
| Text in image | Excellent (incl. non-Latin) | Good, less dense |
| Public figures | Allowed | Often blocked |
| Speed | ~3 sec | 10-15 sec |
| Max resolution | ~1536x1024 | 4K (NB2 and Pro) |
| Variants per call | n=4 possible | Parallel calls needed |
| Native chat sessions | No (edit-chain) | Yes (thought signatures) |
| Reference images | Yes (image.edit) | Yes (up to 14 for Pro) |
| Edit with mask | Yes | No (semantic inpainting via prompt) |
| Grounding on real-time data | No | Yes (Google Search) |
| Watermark | No | SynthID (invisible) |

## What is NOT in this skill (deliberately)

- `input_fidelity` GPT parameter (always auto-high)
- Gemini `includeThoughts` (debug-only)
- Files API for edit (inline_data is enough <20MB)
- Image search grounding separate from web search grounding
