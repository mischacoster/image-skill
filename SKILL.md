---
name: image
description: Dual-provider image generator (OpenAI GPT-Image-2 + Google Gemini Nano Banana). Gebruik deze skill voor alle image-creatie behalve wanneer de gebruiker expliciet een andere skill of MCP noemt. Detecteer of de gebruiker conceptueel verkent (--concept, dual, ALTIJD met diverse prompts), een final asset wil (--hq), text-rich content (--text), een product in setting wil plaatsen (--reference), of itereert op een eerder resultaat (--session). Bij user-attached images: automatisch edit-mode.
tools:
  - Bash
  - Read
---

# Dual-Provider Image Generator (GPT-Image-2 + Gemini Nano Banana)

Eén skill, twee providers, één Claude die kiest op basis van de briefing. De skill biedt bouwstenen, Claude orchestreert de combinatie. Default mindset: zo min mogelijk vragen, maar wel de juiste keuzes maken.

## Beslis-flow

### 1. Eerste check: heb ik genoeg om te beginnen?

Als de gebruiker alleen "image" typt zonder verdere context: vraag in natuurlijke taal naar het onderwerp en de stijl-richting. Bijvoorbeeld:

> "Waar moet het beeld over gaan? Heb je al een stijl-richting in gedachten, bijvoorbeeld fotorealistisch, editorial illustratie, minimalistisch, 3D, cartoon, of zoiets?"

Wacht op antwoord voor je verdergaat.

Als de gebruiker wel een onderwerp geeft maar geen stijl noemt EN er is geen reference image: stel via `ask_user_input_v0` (of natuurlijke vraag) de stijl-vraag voordat je 4 concepten genereert. Reden: bij `--concept` formuleer ik anders vier verschillende stijlen, maar als Mischa al een stijl in zijn hoofd heeft, vallen er drie automatisch af. Liever even checken.

Bij wel een stijl genoemd in de briefing (bijvoorbeeld "editorial vector illustratie" of "fotorealistisch portret") of bij een reference image die de stijl impliceert: ga direct door zonder stijl-vraag.

### 2. Type detecteren

Concept-modus (`--concept`) bij briefings met:
- "concept", "concepten", "ideeen", "verkennen", "brainstorm"
- "varianten", "richting bepalen", "wat past"
- "laat me eens wat zien"
- vage of brede beschrijvingen

HQ-modus (`--hq`) bij briefings met:
- "final", "definitief", "voor productie", "voor publicatie"
- "hoge kwaliteit", "scherp", "print"

Text-modifier (`--text`) bij briefings die noemen:
- "infographic", "diagram", "schema met labels"
- "headline X", "titel Y", "tekst Z in beeld"
- "column-illustratie met kop"

Reference-modus (`--reference`):
- "plaats dit product in..."
- "gebruik deze [logo/foto/character] in een nieuwe scene"
- "in dezelfde stijl als..."

Edit-modus (`--edit`) wanneer de gebruiker een image meestuurt met aanpassingsverzoek.

Session-modus (`--session`/`--continue`):
- "borduur voort op...", "ga verder met...", "nu nog X toevoegen"
- vervolgvragen op een eerdere generatie

### 3. Provider kiezen op basis van use case

Default voor `--concept` zonder verdere indicatie: dual mode (2 GPT + 2 Gemini). Voor andere modes: gebruik de matrix hieronder.

| Briefing-signaal | Provider | Reden |
|---|---|---|
| Infographic, poster met tekst-elementen, UI mockup | **GPT** | Text rendering, spatial logic, instructie-trouw |
| Hyperrealistisch portret, huid-textuur, productfotografie | **Gemini Pro** | Subsurface scattering, natural skin, "real camera" |
| Style transfer (pop-art, watercolor, dramatic b/w, vintage) | **Gemini Pro** | Style transfer is sterker, minder "plastic AI look" |
| Cinematic atmosphere, mood, lighting (geen tekst) | **Gemini Pro** | Atmosfeer en lichtval |
| Logo upload → product icons (brand visual system) | **Gemini Pro** | Tot 14 referenties voor consistency |
| Strikt brand-rule volgen (exact kleur, exact font) | **GPT** | Hoger op instructie-trouwheid |
| Foto's combineren tot één scene (multi-image fusion) | **Gemini Pro** | Mature multi-image fusion |
| Bestaande foto editen, mensen weghalen, scene aanpassen | **GPT** | Stabiele iteratieve edits + face fidelity |
| Herkenbare echte persoon (Mischa, kinderen, klanten) in scene | **GPT** | Face fidelity, identity preservation |
| Publiek figuur (politicus, CEO, etc.) | **GPT** | Gemini blokt vaak met policy-melding |
| Snelheid prioriteit, veel iteraties | **GPT** | 3 sec vs 10-15 sec |
| Non-Latin tekst (Kanji, Cyrillisch, Arabisch) | **GPT** | Multilingual text fidelity hoger |
| Editorial layout, complex grid, magazine-stijl | **GPT** | Layout-kennis sterker |

Bij twijfel tussen twee: vraag de gebruiker, of run beide via dual mode (alleen mogelijk zonder reference image).

### 4. Aanvullende vragen stellen (max 2 per turn)

Stel alleen vragen die echt het resultaat veranderen. Twee vragen is het maximum.

Wel vragen:
- Stijl-richting als geen reference image en geen stijl in briefing
- Oriëntatie/aspect ratio als briefing geen vorm noemt en context niet duidelijk is
- Provider keuze als de briefing tussen GPT- en Gemini-sterktes balanceert

Niet vragen:
- Bij `--concept` met duidelijke stijl-richting of reference: gewoon draaien
- Format, background, compression: gebruik defaults tenzij specifiek relevant
- Aantal varianten: default 4 voor concept, 1 voor hq

### 5. Bij `--concept`: variatie-strategie afstemmen op briefing

Belangrijke fix voor "4 concepten die eigenlijk 2 ideeën zijn": gebruik altijd `--prompts` met vier echt verschillende prompts. Maar de variatie-as kiezen:

**Als geen stijl-richting genoemd door gebruiker** (en je hebt al gevraagd of niet gevraagd): varieer langs stijl-as (editorial vector / fotorealistisch / 3D isometric / minimalist metaphor).

**Als wel stijl-richting genoemd** ("editorial illustration", "fotorealistisch", "minimalist"): houd stijl constant over alle 4 en varieer langs andere assen:
- Compositie/perspectief (close-up, wide, isometric, dynamic angle)
- Interpretatie (literal, metaforisch, abstract, symbolisch)
- Mood (serene, energetic, dramatic, contemplative)
- Color palette (binnen de gegeven stijl)

**Als reference image meegestuurd**: stijl wordt grotendeels door de reference bepaald. Varieer langs compositie, perspectief, en context (verschillende settings waarin het reference-onderwerp zich bevindt).

Variatie-assen om uit te kiezen (combineer twee tegelijk voor maximale spreiding):
- Stijl: editorial vector / photorealism / 3D isometric / pencil sketch / vector flat / watercolor / technical diagram / claymation / low-poly
- Compositie: close-up / wide shot / isometric / top-down / first person / dynamic asymmetric
- Interpretatie: literal / metaphorical / abstract / symbolic / narrative scene
- Mood: serene / energetic / dramatic / playful / minimalist / dystopian
- Medium: digital / sketch / watercolor / 3D render / photography / collage
- Color palette: high-contrast / monochrome / vibrant / muted earth / two-tone / single accent

Voor Mischa specifiek: contrast-rijke palettes, geen rood-groen combinaties (kleurenblind).

## Provider-caveats (belangrijk om mee te wegen)

**Public figures**: Gemini blokt prompts met herkenbare bekende personen (politici, CEO's, beroemdheden) met een policy-melding. GPT doet ze wel. Voor zulke prompts altijd `--gpt`.

**Snelheid**: GPT-Image-2 doet ~3 seconden per call, Nano Banana Pro 10-15 seconden. Bij dual mode wordt de wall time bepaald door Gemini.

**Watermerk**: Gemini outputs hebben standaard een SynthID watermerk (onzichtbaar maar detecteerbaar). GPT heeft dit niet. Voor de meeste use cases irrelevant, maar bij forensische analyse of als watermark verstoring een issue is: GPT.

**Editorial vs fotorealistisch trade-off**: GPT levert vaak "polished, clean, slightly digital painting" output. Gemini levert vaak "natural, less AI-polished, photographic" output. Kies op basis van wat je nodig hebt.

**4K**: Gemini ondersteunt native 4K vanaf NB2. GPT-Image-2 zit op ongeveer 1536x1024 max.

## Concept → final met consistency

Pro is default voor medium en high quality. Voor low (concept) blijft het NB2 omdat alleen NB2 op 512px kan. Drie strategieën om consistency te behouden tussen concept en final:

**Optie 1, concept als reference**:
```bash
# Concept (NB2 op 512)
python3 ~/.claude/skills/image/generate.py "logo voor Grey Matters" --concept --prompts "..."

# Final met goedgekeurde concept als reference (Pro op 4K)
python3 ~/.claude/skills/image/generate.py "produceer hi-res productieversie, identieke compositie en stijl" --reference 2026-05-16_..._gemini_v2.png --gemini --quality high
```

**Optie 2, sessie**:
```bash
python3 ~/.claude/skills/image/generate.py "logo voor Grey Matters" --session logo-gm --gemini --quality medium
python3 ~/.claude/skills/image/generate.py "nu in 4K, exact dezelfde compositie" --continue --quality high
```

**Optie 3, blijf bij NB2**:
```bash
python3 ~/.claude/skills/image/generate.py "logo voor Grey Matters" --hq --gemini --gemini-model nb2 --resolution 4K
```

## Reference-modus (product in setting, herkenbare persoon)

Voor "plaats dit in setting X" of "deze persoon in deze scene":

```bash
# Product in nieuwe locatie
python3 ~/.claude/skills/image/generate.py "plaats deze parfumfles op marmeren badkamerblad met zacht natuurlijk licht" --reference parfum.jpg --gemini --quality high

# Herkenbare persoon in scene (GPT vanwege face fidelity)
python3 ~/.claude/skills/image/generate.py "deze persoon als illusionist in een vol theater met vuurbal" --reference foto.jpg --gpt --hq

# Multi-reference compositie
python3 ~/.claude/skills/image/generate.py "draag dit logo op een wit t-shirt, gedragen door dit model" --reference logo.png --reference model.jpg --gemini --quality high
```

Provider-keuze bij reference image:
- Reference is een **herkenbare echte persoon** die identiek moet blijven → **GPT** (face fidelity)
- Reference is een **product** dat in een nieuwe scene moet → **Gemini** (compositie sterker)
- Reference is een **logo of brand-asset** → **Gemini** (multi-reference mature)
- Reference is een **fictief karakter** dat herkenbaar moet blijven over scenes → **Gemini** (character continuity)

## Edit-modus (aanpassen van een bestaande image)

Wanneer de gebruiker een image attacht en om een aanpassing vraagt:
1. Detecteer de file path
2. Pass door aan `--edit`
3. Forceer provider op basis van wat er moet:
   - Aanpassing met behoud van herkenbare persoon: `--gpt`
   - Style transfer of atmosfeer-aanpassing: `--gemini`
   - Mensen weghalen, scene compositie aanpassen, iteratieve edits: `--gpt`
4. `--skipquestions` om geen extra vragen te stellen

```bash
python3 ~/.claude/skills/image/generate.py "verwijder de andere personen op het plein, zodat alleen deze persoon overblijft" --edit /path/to/photo.jpg --gpt --skipquestions
```

## Multi-turn sessions (iteratief door-itereren)

```bash
# Start sessie
python3 ~/.claude/skills/image/generate.py "futuristisch dashboard, dark mode" --session finadvice-ui --gemini --quality medium

# Iteraties binnen sessie
python3 ~/.claude/skills/image/generate.py "voeg een grafiek toe rechts" --continue
python3 ~/.claude/skills/image/generate.py "warmer kleurpalet" --continue

# Beheer
python3 ~/.claude/skills/image/generate.py --list-sessions
python3 ~/.claude/skills/image/generate.py --reset-session finadvice-ui
```

State per project-folder in `./.image-sessions/{name}.json`. Voor Gemini: echte chat API met thought signatures. Voor GPT: edit-chain met laatste output als input.

## Gedrag na generatie

Snelheid van levering boven analyse. Toon de bestanden met kortst mogelijke bevestiging:

- Voor `--concept`: "4 concepten klaar, gevarieerd langs [stijl/compositie/etc]"
- Voor `--hq`: "Hier is je hi-res asset"
- Voor sessions: "Turn 3 in [sessie-naam]"

Geen analyse, vergelijking of suggesties tenzij gevraagd. Sluit altijd af met:

> *"Wil je dat ik de afbeeldingen analyseer of een specifieke richting verder uitwerk?"*

Alleen bij expliciete vraag om analyse, kritiek of prompt-verbetering geef je die in detail.

## First-time setup

```bash
pip3 install openai google-genai pillow
```

Open `generate.py` en plak je API keys bovenaan:
- `OPENAI_API_KEY = "sk-proj-..."`
- `GEMINI_API_KEY = "AIza..."`

## Presets en modifier

| Naam | Type | Default providers | Variants | Quality | Use case |
|---|---|---|---|---|---|
| `--concept` | preset | dual | 4 (2+2) | low | Snel verkennen met diverse prompts |
| `--hq` | preset | kies expliciet | 1 | high | Final asset |
| `--web` | preset | kies expliciet | 2 | medium | Web asset |
| `--social` | preset | kies expliciet | 4 | medium | Social media |
| `--text` | modifier | (volgt preset) | (volgt preset) | (volgt preset) | Force Gemini Pro |

`--text` is een modifier en combineert met elk preset. Bij `--concept --text` bumpt de Gemini-zijde van 512 naar 1K (Pro kan geen 512).

## Quality mapping voor Gemini

| Quality | Resolution | Model | Note |
|---|---|---|---|
| low | 512 | NB2 | Pro kan geen 512, dus altijd NB2 |
| medium | 1K | Pro | Default Pro |
| high | 4K | Pro | Default Pro |

Met `--text`: low wordt 1K + Pro, medium en high blijven 1K/4K + Pro.

## Voorbeelden van invocaties

```bash
# Dual concept met diverse prompts (zonder stijl-richting)
python3 ~/.claude/skills/image/generate.py "een illustratie voor Status Quo Bias column" --concept --prompts "editorial vector style, person frozen at fork in road|metaphorical photorealistic, anchor pulling someone down|3D isometric scene of comfort zone|abstract minimalist composition with weights"

# Dual concept met stijl-richting al gegeven: varieer op andere assen
python3 ~/.claude/skills/image/generate.py "editorial vector illustration voor mijn Confirmation Bias column" --concept --prompts "person looking through colored glasses at a book, close-up|cluttered desk with selective post-it markings, top-down|silhouettes against a wall of TVs showing same news, wide|two paths diverging with one brightly lit, isometric"

# Hi-quality final met GPT (sterke instructie-trouw, brand assets)
python3 ~/.claude/skills/image/generate.py "minimalistisch logo voor Grey Matters, geometric brain icon" --hq --gpt

# Hi-quality fotorealistisch met Gemini Pro
python3 ~/.claude/skills/image/generate.py "moderne lifestyle scene van iemand die thuis werkt aan de keukentafel, ochtendlicht" --hq --gemini

# Infographic met tekst (GPT vanwege text rendering)
python3 ~/.claude/skills/image/generate.py "infographic over confirmation bias met heldere labels en titel" --text --gpt --hq

# Product in nieuwe setting
python3 ~/.claude/skills/image/generate.py "plaats deze fles op natuursteen aanrecht, ochtendlicht" --reference fles.jpg --gemini --quality high

# Herkenbare persoon in scene (GPT vanwege face fidelity)
python3 ~/.claude/skills/image/generate.py "deze persoon als spreker op een TEDx podium, donkere achtergrond met TEDx logo" --reference foto.jpg --gpt --hq

# Mensen weghalen uit foto (GPT vanwege stabiele edits)
python3 ~/.claude/skills/image/generate.py "verwijder alle andere personen rond de centrale persoon, alsof zij de enige is op het plein" --edit foto.jpg --gpt --skipquestions

# Banner met aspect ratio
python3 ~/.claude/skills/image/generate.py "banner LinkedIn artikel over biases" --gemini --aspect-ratio 21:9 --quality high

# Met grounding voor real-time data
python3 ~/.claude/skills/image/generate.py "visualiseer huidige rente-ontwikkeling 12 maanden" --gemini --grounding --quality high

# Sessie voor iteratie
python3 ~/.claude/skills/image/generate.py "futuristisch dashboard, dark mode" --session dash --gemini --quality medium
python3 ~/.claude/skills/image/generate.py "voeg grafiek rechts toe" --continue
python3 ~/.claude/skills/image/generate.py "warmer kleurpalet" --continue
```

## Alle switches

**Presets** (kies max 1): `--concept`, `--hq`, `--web`, `--social`

**Modifier** (combineerbaar): `--text` (Gemini Pro forceren)

**Provider** (kies max 1): `--gpt`, `--gemini`

**Generic:**
- `--size square|landscape|portrait|auto`
- `--aspect-ratio` (Gemini-specific)
- `--quality low|medium|high`
- `--variants N` / `-n N`
- `--format png|jpeg|webp` (GPT)

**Diverse prompts:** `--prompts "p1|p2|p3|p4"`

**Gemini:** `--resolution 512|1K|2K|4K`, `--gemini-model flash|nb2|pro|auto`, `--grounding`

**GPT:** `--background auto|opaque`, `--moderation auto|low`, `--compression 0-100`

**Reference/edit (single-provider):** `--reference IMAGE` (meerdere mogelijk), `--edit IMAGE`, `--edit-latest [DIR]`, `--mask IMAGE`

**Sessions (single-provider):** `--session NAME`, `--continue`, `--reset-session NAME`, `--list-sessions`

**Workflow:** `--skipquestions`

## Output

In current working directory:
- `2026-05-16_141523_jouw-prompt-slug_gpt_v1.png`
- `2026-05-16_141523_jouw-prompt-slug_gemini_v1.png`
- `2026-05-16_141523_jouw-prompt-slug_gemini_dash.png` (session-tagged)
- `.txt` sidecar per image met prompt + settings

## Provider-eigenschappen samenvatting

| Eigenschap | GPT-Image-2 | Gemini Nano Banana |
|---|---|---|
| Beste voor | Text, layout, identity preservation, iteratieve edits | Fotorealisme, atmosphere, style transfer, multi-reference |
| Tekst in beeld | Excellent (incl. non-Latin) | Goed, minder dense |
| Public figures | Toegestaan | Vaak geblokt |
| Speed | ~3 sec | 10-15 sec |
| Max resolutie | ~1536x1024 | 4K (NB2 en Pro) |
| Variants per call | n=4 mogelijk | Parallelle calls nodig |
| Native chat sessions | Nee (edit-chain) | Ja (thought signatures) |
| Reference images | Ja (image.edit) | Ja (tot 14 voor Pro) |
| Edit met mask | Ja | Nee (semantic inpainting via prompt) |
| Grounding op real-time data | Nee | Ja (Google Search) |
| Watermerk | Nee | SynthID (onzichtbaar) |

## Wat NIET in deze skill zit (bewust)

- `input_fidelity` GPT-parameter (altijd auto-high)
- Gemini `includeThoughts` (debug-only)
- Files API voor edit (inline_data is genoeg <20MB)
- Image search grounding apart van web search grounding
