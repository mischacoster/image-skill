# Provider Matrix

Use this file to pick between GPT and Gemini when the briefing is ambiguous,
and to understand the trade-offs that aren't obvious from the CLI itself.

## Decision matrix: briefing signal → provider

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
| Character-consistent set (n=2-8 variants of same subject) | **GPT** | gpt-image-2 batches preserve identity across the set |
| Transparent background (logos, cutouts) | **GPT (`--nobg`)** | Auto-routes to gpt-image-1.5 (gpt-image-2 doesn't support transparent) |
| Native 2K output without upscaling | **GPT (`--gpt-2K`)** | gpt-image-2 generates 2K natively; Gemini Pro does 4K |

When in doubt between two: ask the user, or run both via dual mode (only possible
without a reference image).

## Provider caveats

**Public figures**: Gemini blocks prompts featuring recognizable famous people
(politicians, CEOs, celebrities) with a policy message. GPT does them. Always
use `--gpt` for these.

**Speed**: GPT-Image-2 takes ~3 seconds per call, Nano Banana Pro 10-15 seconds.
In dual mode, wall time is determined by Gemini.

**Watermark**: Gemini outputs carry a SynthID watermark by default (invisible
but detectable). GPT does not. Irrelevant for most use cases, but use GPT if
forensic analysis matters or watermark interference is a problem.

**Editorial vs photorealistic trade-off**: GPT often delivers "polished, clean,
slightly digital painting" output. Gemini often delivers "natural, less
AI-polished, photographic" output. Choose based on what you need.

**Native resolution**: Gemini Pro supports 4K. GPT-Image-2 supports native 2K
via `--gpt-2K` (square 2048x2048, landscape 2560x1440, portrait 1440x2560).
For higher than 2K on GPT, upscale externally.

**Transparent background**: gpt-image-2 does *not* support `background: transparent`.
The skill auto-routes `--nobg` to `gpt-image-1.5` (the prior generation). Gemini
has no transparent-bg flag at all.

**GPT-Image-2 edit-chain noise**: After ~3 successive refinements in the same
`--session`, gpt-image-2 can amplify subtle noise/artifacts. The skill prints
a warning from turn 4 onward. If quality degrades, reset the session and
continue from the latest output as a fresh `--reference`.

## Provider properties summary

| Property | GPT-Image-2 | Gemini Nano Banana |
|---|---|---|
| Best for | Text, layout, identity preservation, iterative edits | Photorealism, atmosphere, style transfer, multi-reference |
| Text in image | Excellent (incl. non-Latin) | Good, less dense |
| Public figures | Allowed | Often blocked |
| Speed | ~3 sec | 10-15 sec |
| Max resolution | 2K native (gpt-image-2 via `--gpt-2K`); 1024x1536 default | 4K (NB2 and Pro) |
| Variants per call | n=2-8 (character-consistent) | Parallel calls needed |
| Native chat sessions | No (edit-chain) | Yes (thought signatures) |
| Reference images | Yes (image.edit) | Yes (up to 14 for Pro) |
| Edit with mask | Yes | No (semantic inpainting via prompt) |
| Grounding on real-time data | No | Yes (Google Search) |
| Watermark | No | SynthID (invisible) |
