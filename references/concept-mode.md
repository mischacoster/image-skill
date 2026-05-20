# Concept Mode: Variation Strategy

Read this when running `--concept` and you need to construct genuinely diverse
prompts (rather than four slight variations of one idea).

## Tune the variation axis to the briefing

Important fix for "4 concepts that are actually 2 ideas": always use `--prompts`
with four genuinely different prompts. But choose the variation axis carefully:

**If the user did not mention a style direction** (and you either asked or didn't):
vary along the style axis (editorial vector / photorealistic / 3D isometric /
minimalist metaphor).

**If a style was mentioned** ("editorial illustration", "photorealistic",
"minimalist"): keep the style constant across all 4 and vary along other axes:
- Composition/perspective (close-up, wide, isometric, dynamic angle)
- Interpretation (literal, metaphorical, abstract, symbolic)
- Mood (serene, energetic, dramatic, contemplative)
- Color palette (within the given style)

**If a reference image was provided**: the style is largely determined by the
reference. Vary along composition, perspective, and context (different settings
in which the reference subject appears).

## Axes to combine (pick two for maximum spread)

- **Style**: editorial vector / photorealism / 3D isometric / pencil sketch /
  vector flat / watercolor / technical diagram / claymation / low-poly
- **Composition**: close-up / wide shot / isometric / top-down / first person /
  dynamic asymmetric
- **Interpretation**: literal / metaphorical / abstract / symbolic /
  narrative scene
- **Mood**: serene / energetic / dramatic / playful / minimalist / dystopian
- **Medium**: digital / sketch / watercolor / 3D render / photography / collage
- **Color palette**: high-contrast / monochrome / vibrant / muted earth /
  two-tone / single accent

> Personal preferences (accessibility needs like color-blindness, preferred
> palettes, brands to avoid) belong in your global `CLAUDE.md`, not in this
> skill. The skill stays neutral so it works for everyone.

## Concept → final with consistency

> The `--quality high` and `--hq` calls below are only for the LAST step,
> when the user has explicitly approved a direction and asked for the final
> production version. During iteration between concept and final, stay at
> medium. See `SKILL.md → Cost discipline`.

Pro is the default for medium and high quality. For low (concept) it stays
NB2 because only NB2 can do 512px. Three strategies to keep consistency
between concept and final:

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

## Concept invocation examples

```bash
# Dual concept with diverse prompts (no style direction given)
python3 ~/.claude/skills/image/generate.py "an illustration for a Status Quo Bias column" --concept --prompts "editorial vector style, person frozen at fork in road|metaphorical photorealistic, anchor pulling someone down|3D isometric scene of comfort zone|abstract minimalist composition with weights"

# Dual concept with style direction given: vary on other axes
python3 ~/.claude/skills/image/generate.py "editorial vector illustration for a Confirmation Bias column" --concept --prompts "person looking through colored glasses at a book, close-up|cluttered desk with selective post-it markings, top-down|silhouettes against a wall of TVs showing same news, wide|two paths diverging with one brightly lit, isometric"
```
