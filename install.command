#!/usr/bin/env bash
# ============================================================================
# Image Skill — macOS installer (dubbelklikbaar)
#
# Niet-technische gebruiker? Dubbelklik op dit bestand in Finder.
# Terminal opent automatisch en de installer doorloopt:
#   1. Python-dependencies installeren
#   2. Je OpenAI- en Gemini-API-keys vragen (verborgen invoer)
#   3. De skill plaatsen in ~/.claude/skills/image/ (voor Claude Code)
#   4. Een image.skill bundel bouwen (voor claude.ai / Claude desktop)
#
# Het Terminal-venster blijft open zodat je de output kunt lezen.
# ============================================================================

# Stop bij elke fout zodat we het niet stilletjes verkeerd doen
set -e

# cd naar de map waar dit script staat (bij dubbelklik is cwd anders je $HOME)
cd "$(dirname "$0")"

# clear: faalt fail-silent in omgevingen zonder TERM (in echte Terminal werkt het)
clear 2>/dev/null || true
cat <<'BANNER'
╭──────────────────────────────────────────────────────────╮
│  Image Skill installer                                   │
│  Dual-provider image generator (GPT + Gemini)            │
╰──────────────────────────────────────────────────────────╯

BANNER

# Verwijder de quarantine-flag van dit bestand voor toekomstige runs.
# (Bij eerste run blokkeert macOS Gatekeeper — die handmatige Open-stap
#  heb je dan al gedaan; dit voorkomt dat het bij elke run terugkomt.)
xattr -d com.apple.quarantine "$0" 2>/dev/null || true

# Python3 check
if ! command -v python3 >/dev/null 2>&1; then
  cat <<'EOF'
✗  Python 3 is niet geïnstalleerd.

   Op macOS is de makkelijkste manier de Command Line Tools:

     1. Open Terminal (Programma's → Hulpprogramma's → Terminal)
     2. Plak en druk Enter:

        xcode-select --install

     3. Bevestig het pop-up en wacht tot de installatie klaar is.
     4. Dubbelklik opnieuw op install.command.

   Alternatief: download Python via https://www.python.org/downloads/

EOF
  echo "Druk op Enter om dit venster te sluiten."
  read -r _
  exit 1
fi

# Check of setup.py er naast staat (zou altijd moeten, maar zekerheid is goedkoop)
if [[ ! -f "setup.py" ]]; then
  cat <<EOF
✗  setup.py niet gevonden naast install.command.

   Dit bestand hoort in dezelfde map te staan als setup.py, SKILL.md en
   generate.example.py. Heb je de ZIP wel volledig uitgepakt?

   Huidige map: $(pwd)

EOF
  echo "Druk op Enter om dit venster te sluiten."
  read -r _
  exit 1
fi

# Forward alle command-line argumenten door naar setup.py (voor power-users
# die install.command "$ ./install.command --no-deps" kunnen aanroepen)
python3 setup.py "$@"
status=$?

echo
echo "──────────────────────────────────────────────────────────"
if [[ $status -eq 0 ]]; then
  echo "✓ Installer afgerond."
else
  echo "✗ Installer beëindigd met fout (exit code $status)."
fi
echo
echo "Druk op Enter om dit venster te sluiten."
read -r _
exit $status
