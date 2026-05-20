# Modes & Invocation Examples

Read this when handling reference mode, edit mode, sessions, or when you need
a concrete invocation example for a specific use case.

## Reference mode (product in setting, recognizable person)

For "place this in setting X" or "this person in this scene":

```bash
# Product in a new location — default medium, NOT HQ
python3 ~/.claude/skills/image/generate.py "place this perfume bottle on a marble bathroom counter with soft natural light" --reference perfume.jpg --gemini

# Recognizable person in scene (GPT for face fidelity) — medium iteration
python3 ~/.claude/skills/image/generate.py "this person as an illusionist in a packed theater with a fireball" --reference photo.jpg --gpt

# Multi-reference composition / merge — medium iteration
python3 ~/.claude/skills/image/generate.py "place this logo on a white t-shirt, worn by this model" --reference logo.png --reference model.jpg --gemini

# Only when user explicitly asks for the final hi-res version, append --hq
python3 ~/.claude/skills/image/generate.py "...same prompt as above..." --reference perfume.jpg --gemini --hq
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
   - Background removal on existing photo: `--gpt --nobg` (routes to gpt-image-1.5)
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

State is stored per project folder in `./.image-sessions/{name}.json`. For Gemini:
real chat API with thought signatures. For GPT: edit-chain with the latest
output as input.

**Note for GPT sessions**: gpt-image-2 edit-chains can accumulate noise after
~3 successive refines. The skill prints a warning at turn 4. If quality degrades,
reset and continue from the latest output as a fresh `--reference`.

## Presets and modifiers

| Name | Type | Default providers | Variants | Quality | Use case |
|---|---|---|---|---|---|
| `--concept` | preset | dual | 4 (2+2) | low | Explore quickly with diverse prompts |
| `--hq` | preset | choose explicitly | 1 | high | Final asset |
| `--web` | preset | choose explicitly | 2 | medium | Web asset |
| `--social` | preset | choose explicitly | 4 | medium | Social media |
| `--text` | modifier | (follows preset) | (follows preset) | (follows preset) | Force Gemini Pro |

`--text` is a modifier and combines with any preset. With `--concept --text`
the Gemini side bumps from 512 to 1K (Pro cannot do 512).

## Quality mapping for Gemini

| Quality | Resolution | Model | Note |
|---|---|---|---|
| low | 512 | NB2 | Pro cannot do 512, so always NB2 |
| medium | 1K | Pro | Default Pro |
| high | 4K | Pro | Default Pro |

With `--text`: low becomes 1K + Pro, medium and high stay 1K/4K + Pro.

## More invocation examples

> **Examples below that include `--hq` show the syntax for FINAL ASSET calls
> only.** For iteration, omit `--hq` to default to medium quality. Never add
> `--hq` automatically — wait for the user to ask explicitly. See
> `SKILL.md → Cost discipline`.

```bash
# Hi-quality final with GPT (use only when user asks for the final version)
python3 ~/.claude/skills/image/generate.py "minimalist logo for a creative studio, geometric brain icon" --hq --gpt

# Hi-quality photorealistic with Gemini Pro
python3 ~/.claude/skills/image/generate.py "modern lifestyle scene of someone working from home at the kitchen table, morning light" --hq --gemini

# Infographic with text (GPT for text rendering)
python3 ~/.claude/skills/image/generate.py "infographic about confirmation bias with clear labels and title" --text --gpt --hq

# Banner with aspect ratio — default medium for iteration
python3 ~/.claude/skills/image/generate.py "LinkedIn article banner about cognitive biases" --gemini --aspect-ratio 21:9

# Transparent PNG logo (routes to gpt-image-1.5)
python3 ~/.claude/skills/image/generate.py "minimalist geometric brain icon, vector style" --gpt --nobg --hq

# Native 2K hi-res asset on gpt-image-2
python3 ~/.claude/skills/image/generate.py "editorial illustration about decision fatigue" --gpt --hq --gpt-2K

# Character-consistent set of 6 variants in one batch
python3 ~/.claude/skills/image/generate.py "founder portrait, four-point lighting, neutral grey backdrop" --gpt --hq --variants 6

# With grounding for real-time data — default medium
python3 ~/.claude/skills/image/generate.py "visualize current 12-month interest rate trend" --gemini --grounding
```
