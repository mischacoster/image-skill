#!/usr/bin/env bash
# ============================================================================
# Image Skill — macOS installer (double-clickable)
#
# Non-technical user? Double-click this file in Finder.
# Terminal opens automatically and the installer walks through:
#   1. Install Python dependencies
#   2. Ask for your OpenAI and Gemini API keys (hidden input)
#   3. Place the skill in ~/.claude/skills/image/ (for Claude Code)
#   4. Build an image.skill bundle (for claude.ai / Claude desktop)
#
# The Terminal window stays open so you can read the output.
# ============================================================================

# Stop on first error so we don't silently do the wrong thing
set -e

# cd to the directory of this script (double-click cwd is otherwise $HOME)
cd "$(dirname "$0")"

# clear: fail-silent in environments without TERM (works in a real Terminal)
clear 2>/dev/null || true
cat <<'BANNER'
╭──────────────────────────────────────────────────────────╮
│  Image Skill installer                                   │
│  Dual-provider image generator (GPT + Gemini)            │
╰──────────────────────────────────────────────────────────╯

BANNER

# Remove the quarantine flag from this file for future runs.
# (On first run macOS Gatekeeper blocks — you handled the manual Open step
#  then; this prevents the prompt every subsequent run.)
xattr -d com.apple.quarantine "$0" 2>/dev/null || true

# Python 3 check
if ! command -v python3 >/dev/null 2>&1; then
  cat <<'EOF'
✗  Python 3 is not installed.

   On macOS the easiest path is the Command Line Tools:

     1. Open Terminal (Applications → Utilities → Terminal)
     2. Paste and press Enter:

        xcode-select --install

     3. Confirm the popup and wait for the install to finish.
     4. Double-click install.command again.

   Alternative: download Python from https://www.python.org/downloads/

EOF
  echo "Press Enter to close this window."
  read -r _
  exit 1
fi

# Sanity check that setup.py is next to us (should always be, but cheap to verify)
if [[ ! -f "setup.py" ]]; then
  cat <<EOF
✗  setup.py not found next to install.command.

   This file should sit in the same directory as setup.py, SKILL.md and
   generate.example.py. Did you unzip the archive completely?

   Current directory: $(pwd)

EOF
  echo "Press Enter to close this window."
  read -r _
  exit 1
fi

# Forward all command-line arguments to setup.py (so power users can do
# "./install.command --no-deps" or similar)
python3 setup.py "$@"
status=$?

echo
echo "──────────────────────────────────────────────────────────"
if [[ $status -eq 0 ]]; then
  echo "✓ Installer finished."
else
  echo "✗ Installer exited with error (exit code $status)."
fi
echo
echo "Press Enter to close this window."
read -r _
exit $status
