# Image Skill — Dual-Provider Image Generator

Eén Claude Code skill, twee image-providers: **OpenAI GPT-Image-2** en
**Google Gemini Nano Banana (Pro)**. Claude kiest zelf de juiste provider en
modus op basis van de briefing — de skill levert de bouwstenen, Claude
orchestreert.

> Bedoeld als drop-in skill voor Claude Code / claude.ai. Werkt ook als
> standalone CLI-script.

---

## ⚠️ API-keys eerst lezen

Dit script praat met betaalde API's (OpenAI + Google Gemini). De keys zijn
**niet** in deze repo opgenomen.

- **`generate.py`** = het werkende script, mét jouw keys. Staat in
  [.gitignore](.gitignore) en wordt **nooit** gecommit.
- **`generate.example.py`** = exact hetzelfde script, maar met lege keys. Dit
  is wat je in de repo ziet.

Bij installatie kopieer je het template naar `generate.py` en vul je daar je
eigen keys in. Zo kan een key nooit per ongeluk op GitHub belanden.

Waarom de keys *in het bestand* mogen (en niet alleen als environment
variable): de skill draait ook via **claude.ai / Cowork**, en daar zijn geen
shell environment variables beschikbaar. Het script ondersteunt beide: een
ingevulde key in het bestand óf de env vars `OPENAI_API_KEY` /
`GEMINI_API_KEY` (de env var wordt gebruikt als de key in het bestand leeg is).

---

## Vereisten

- Python 3.9+
- Een OpenAI API-key (met toegang tot GPT-Image-2)
- Een Google Gemini API-key (met toegang tot Nano Banana / NB2 / Pro)
- Python-packages: `openai`, `google-genai`, `pillow`

---

## Installatie

### Niet-technisch & op macOS? Dubbelklik

Krijg je deze repo als ZIP? Pak hem uit en **dubbelklik op `install.command`**
in Finder. Terminal opent automatisch en doorloopt de installatie. Niets
typen, geen commando's onthouden.

> **Eerste keer:** macOS Gatekeeper kan zeggen *"cannot be opened because
> it is from an unidentified developer"*. Klik dan met de rechtermuisknop
> op `install.command` → **Open** → **Open**. Dat hoeft maar één keer.
>
> **Lukt dubbelklikken niet?** (Bijv. omdat de uitvoerrechten verloren
> gingen tijdens het uitpakken.) Open Terminal, sleep `install.command`
> erin, druk op Enter.

### Aanbevolen: via het setup-script (alle platforms)

```bash
git clone https://github.com/mischacoster/image-skill.git
cd image-skill
./setup.py
```

Het script vraagt interactief om je OpenAI- en Gemini-key (verborgen invoer,
niet in shell-history), installeert de Python-dependencies, plaatst de skill
in `~/.claude/skills/image/` voor **Claude Code**, en bouwt een
`image.skill` bundel die je in **claude.ai** of de **Claude desktop app**
kunt importeren via *Settings → Skills*.

Handige flags:

```bash
./setup.py --no-deps          # skip pip install (al gedaan)
./setup.py --no-local         # alleen bundel, geen lokale install
./setup.py --no-bundle        # alleen lokale install, geen bundel
./setup.py --bundle-path ~/Desktop/image.skill
./setup.py --yes              # accepteer alle bevestigingen
./setup.py --help
```

> **⚠ Security:** het `image.skill` bestand bevat je betaalde API-keys.
> Behandel het als een wachtwoord — niet committen, niet in iCloud/Dropbox,
> niet zonder reden doorsturen. Iedereen met dit bestand kan API-calls op
> jouw rekening doen. Het script schrijft het bestand met permissies `600`
> (alleen jij kunt het lezen).

### Importeren in claude.ai of Claude desktop

1. Open *Settings → Skills* (of *Capabilities → Skills*).
2. Kies *Create skill* / *Upload* en selecteer `image.skill`.
3. Eerste call in een nieuwe sessie: de sandbox installeert automatisch de
   Python-deps (~10–20s overhead). Daarna draait het normaal.

### Handmatig (zonder setup-script)

```bash
git clone https://github.com/mischacoster/image-skill.git ~/.claude/skills/image
cd ~/.claude/skills/image
pip3 install openai google-genai pillow
cp generate.example.py generate.py
```

Open `generate.py` en vul bovenin (regels 75–76) je keys in:

```python
OPENAI_API_KEY = "sk-proj-..."   # jouw OpenAI key
GEMINI_API_KEY = "AIza..."       # jouw Gemini key
```

Of laat ze leeg en zet environment variables:

```bash
export OPENAI_API_KEY="sk-proj-..."
export GEMINI_API_KEY="AIza..."
```

Standalone draaien werkt ook:

```bash
python3 ~/.claude/skills/image/generate.py "een minimalistisch brein-logo" --hq --gpt
```

---

## Gebruik in het kort

Claude detecteert automatisch wat je nodig hebt en kiest provider + modus.
Je kunt ook expliciet sturen met de switches hieronder.

| Modus | Trigger | Wat het doet |
|---|---|---|
| **Concept** (`--concept`) | "verken", "ideeën", "varianten", vage briefing | 4 diverse concepten, dual (2 GPT + 2 Gemini), snel/low-res |
| **HQ** (`--hq`) | "final", "definitief", "print", "hoge kwaliteit" | 1 hi-res asset |
| **Web** (`--web`) | web-asset | 2 varianten, medium |
| **Social** (`--social`) | social media | 4 varianten, medium |
| **Text** (`--text`) | infographic, labels, headline in beeld | modifier, forceert Gemini Pro (combineert met elk preset) |
| **Reference** (`--reference IMG`) | "plaats dit product in…", "deze persoon in scene" | genereert op basis van 1+ referentiebeelden |
| **Edit** (`--edit IMG`) | bestaande afbeelding aanpassen | edit een meegestuurde afbeelding |
| **Session** (`--session NAME` / `--continue`) | "borduur voort op…", iteraties | multi-turn, behoudt context tussen calls |

---

## Provider kiezen

Default voor `--concept`: dual mode (2 GPT + 2 Gemini). Voor de rest geldt:

| Briefing-signaal | Provider | Reden |
|---|---|---|
| Infographic, poster met tekst, UI mockup | **GPT** | Text rendering, spatial logic, instructie-trouw |
| Hyperrealistisch portret, productfotografie | **Gemini Pro** | Natuurlijke huid, "real camera" |
| Style transfer (pop-art, watercolor, vintage) | **Gemini Pro** | Sterkere style transfer |
| Cinematic sfeer, mood, lighting (geen tekst) | **Gemini Pro** | Atmosfeer en lichtval |
| Strikt brand-rule volgen (exacte kleur/font) | **GPT** | Hoger op instructie-trouw |
| Foto's combineren tot één scene | **Gemini Pro** | Mature multi-image fusion |
| Bestaande foto editen, mensen weghalen | **GPT** | Stabiele iteratieve edits |
| Herkenbare echte persoon in scene | **GPT** | Face fidelity / identity preservation |
| Publiek figuur (politicus, CEO) | **GPT** | Gemini blokt vaak met policy-melding |
| Snelheid + veel iteraties | **GPT** | ~3 sec vs 10–15 sec |
| Non-Latin tekst (Kanji, Cyrillisch, Arabisch) | **GPT** | Multilingual text fidelity |
| Editorial layout, complex grid | **GPT** | Layout-kennis sterker |

---

## Alle switches

**Presets** (kies max 1): `--concept` · `--hq` · `--web` · `--social`

**Modifier** (combineerbaar): `--text` (forceert Gemini Pro)

**Provider** (kies max 1): `--gpt` · `--gemini`

**Generiek:**
- `--size square|landscape|portrait|auto`
- `--aspect-ratio` (Gemini-specifiek)
- `--quality low|medium|high`
- `--variants N` / `-n N`
- `--format png|jpeg|webp` (GPT)

**Diverse prompts:** `--prompts "p1|p2|p3|p4"` (4 echt verschillende prompts)

**Gemini:** `--resolution 512|1K|2K|4K` · `--gemini-model flash|nb2|pro|auto` · `--grounding`

**GPT:** `--background auto|opaque` · `--moderation auto|low` · `--compression 0-100`

**Reference / edit** (single-provider): `--reference IMG` (meerdere mogelijk) · `--edit IMG` · `--edit-latest [DIR]` · `--mask IMG`

**Sessions** (single-provider): `--session NAME` · `--continue` · `--reset-session NAME` · `--list-sessions`

**Workflow:** `--skipquestions`

### Quality-mapping (Gemini)

| Quality | Resolutie | Model | Noot |
|---|---|---|---|
| low | 512 | NB2 | Pro kan geen 512 |
| medium | 1K | Pro | Default Pro |
| high | 4K | Pro | Default Pro |

Met `--text` wordt low automatisch 1K + Pro.

---

## Voorbeelden

```bash
# Dual concept met diverse prompts
python3 ~/.claude/skills/image/generate.py "illustratie voor Status Quo Bias column" \
  --concept --prompts "editorial vector, person frozen at fork in road|metaphorical photorealistic, anchor pulling someone down|3D isometric comfort zone|abstract minimalist with weights"

# Hi-quality logo met GPT (sterke instructie-trouw)
python3 ~/.claude/skills/image/generate.py "minimalistisch logo, geometric brain icon" --hq --gpt

# Fotorealistische lifestyle scene met Gemini Pro
python3 ~/.claude/skills/image/generate.py "iemand werkt thuis aan de keukentafel, ochtendlicht" --hq --gemini

# Infographic met tekst (GPT vanwege text rendering)
python3 ~/.claude/skills/image/generate.py "infographic over confirmation bias met labels en titel" --text --gpt --hq

# Product in nieuwe setting
python3 ~/.claude/skills/image/generate.py "plaats deze fles op natuursteen aanrecht, ochtendlicht" --reference fles.jpg --gemini --quality high

# Herkenbare persoon in scene (GPT vanwege face fidelity)
python3 ~/.claude/skills/image/generate.py "deze persoon als spreker op een TEDx podium" --reference foto.jpg --gpt --hq

# Mensen weghalen uit foto
python3 ~/.claude/skills/image/generate.py "verwijder alle andere personen rond de centrale persoon" --edit foto.jpg --gpt --skipquestions

# Banner met aspect ratio
python3 ~/.claude/skills/image/generate.py "LinkedIn banner over biases" --gemini --aspect-ratio 21:9 --quality high

# Iteratieve sessie
python3 ~/.claude/skills/image/generate.py "futuristisch dashboard, dark mode" --session dash --gemini --quality medium
python3 ~/.claude/skills/image/generate.py "voeg grafiek rechts toe" --continue
python3 ~/.claude/skills/image/generate.py "warmer kleurpalet" --continue
```

---

## Output

Bestanden komen in de huidige werkmap:

- `2026-05-16_141523_jouw-prompt-slug_gpt_v1.png`
- `2026-05-16_141523_jouw-prompt-slug_gemini_v1.png`
- `2026-05-16_141523_jouw-prompt-slug_gemini_dash.png` (session-tagged)
- Een `.txt` sidecar per afbeelding met de gebruikte prompt + settings

Sessie-state staat per projectmap in `./.image-sessions/{name}.json`.

> Gegenereerde afbeeldingen, sidecars en sessie-state staan in
> [.gitignore](.gitignore) en worden bewust niet meegecommit.

---

## Provider-eigenschappen

| Eigenschap | GPT-Image-2 | Gemini Nano Banana |
|---|---|---|
| Beste voor | Tekst, layout, identity preservation, iteratieve edits | Fotorealisme, atmosfeer, style transfer, multi-reference |
| Tekst in beeld | Excellent (incl. non-Latin) | Goed, minder dense |
| Public figures | Toegestaan | Vaak geblokt |
| Snelheid | ~3 sec | 10–15 sec |
| Max resolutie | ~1536×1024 | 4K (NB2 en Pro) |
| Native chat sessions | Nee (edit-chain) | Ja (thought signatures) |
| Reference images | Ja (image.edit) | Ja (tot 14 voor Pro) |
| Edit met mask | Ja | Nee (semantic inpainting via prompt) |
| Grounding op real-time data | Nee | Ja (Google Search) |
| Watermerk | Nee | SynthID (onzichtbaar) |

---

## Troubleshooting

| Probleem | Oplossing |
|---|---|
| `No OpenAI API key` / `No Gemini API key` | Key niet ingevuld in `generate.py` én geen env var gezet. Vul één van beide. |
| `ModuleNotFoundError: openai` | `pip3 install openai google-genai pillow` |
| Claude ziet de skill niet | Repo moet in `~/.claude/skills/image/` staan en `SKILL.md` bevatten |
| Gemini weigert een bekende persoon | Gebruik `--gpt` (Gemini blokt publieke figuren) |
| `generate.py` verschijnt in `git status` | Dat hoort niet — controleer dat [.gitignore](.gitignore) de regel `generate.py` bevat |

---

## Bestanden in deze repo

| Bestand | Rol |
|---|---|
| `SKILL.md` | Skill-instructies voor Claude (beslis-flow, provider-keuze) |
| `generate.example.py` | Het script zónder keys — kopieer naar `generate.py` |
| `generate.py` | Jouw werkende script mét keys — **niet** in git (`.gitignore`) |
| `setup.py` | Setup-script: deps, keys, lokale install + bundel-build |
| `install.command` | macOS dubbelklik-launcher voor `setup.py` (non-tech) |
| `image.skill` | Gegenereerde bundel mét keys — **niet** in git (`.gitignore`) |
| `README.md` | Dit bestand |
| `.gitignore` | Houdt keys, output, bundel en sessie-state buiten git |
