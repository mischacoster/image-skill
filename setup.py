#!/usr/bin/env python3
"""
Image Skill — setup script.

Installs dependencies, asks for API keys, places the skill in
~/.claude/skills/image/ (for Claude Code) and builds an image.skill bundle
that you can import into claude.ai / Claude desktop.

Security: the generated image.skill file contains your paid API keys.
Treat it like a password — don't commit it, don't put it in iCloud/Dropbox,
don't share it.

Examples:
  ./setup.py                       # interactive, everything in one run
  ./setup.py --no-deps             # skip pip install
  ./setup.py --no-local            # bundle only, no ~/.claude/skills install
  ./setup.py --no-bundle           # local install only
  ./setup.py --bundle-path ~/Desktop/image.skill
  ./setup.py --yes                 # accept all prompts (CI / scripted)
"""

from __future__ import annotations

import argparse
import getpass
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

# ----------------------------------------------------------------------------
# Repo location (where this script lives) and the skill install directory
# ----------------------------------------------------------------------------
REPO_DIR = Path(__file__).resolve().parent
TEMPLATE = REPO_DIR / "generate.example.py"
SKILL_MD = REPO_DIR / "SKILL.md"
SKILL_INSTALL_DIR = Path.home() / ".claude" / "skills" / "image"
PIP_PACKAGES = ["openai", "google-genai", "pillow"]


# ----------------------------------------------------------------------------
# Small TUI helpers (no external deps)
# ----------------------------------------------------------------------------
def step(msg: str) -> None:
    print(f"\n==> {msg}")


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def warn(msg: str) -> None:
    print(f"  ⚠ {msg}")


def fail(msg: str) -> None:
    print(f"  ✗ {msg}", file=sys.stderr)


def confirm(prompt: str, default: bool, assume_yes: bool) -> bool:
    if assume_yes:
        return True
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        raw = input(f"  {prompt} {suffix}: ").strip().lower()
        if not raw:
            return default
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False


def read_key(label: str, expect_prefix: tuple[str, ...]) -> str:
    """Ask for an API key via getpass (input hidden, not in shell history)."""
    while True:
        key = getpass.getpass(f"  {label}: ").strip()
        if len(key) < 20:
            warn("Looks too short for a valid key. Try again.")
            continue
        if not any(key.startswith(p) for p in expect_prefix):
            warn(f"Expected prefix {' or '.join(expect_prefix)}.")
            if not confirm("Continue with this value anyway?", default=False, assume_yes=False):
                continue
        return key


# ----------------------------------------------------------------------------
# Steps
# ----------------------------------------------------------------------------
def check_prerequisites() -> None:
    missing = []
    if not TEMPLATE.exists():
        missing.append(str(TEMPLATE))
    if not SKILL_MD.exists():
        missing.append(str(SKILL_MD))
    if missing:
        fail("Required files not found:")
        for m in missing:
            print(f"      {m}", file=sys.stderr)
        print(
            "\n  Run this script from the cloned image-skill repo.\n"
            "  (git clone https://github.com/mischacoster/image-skill.git)",
            file=sys.stderr,
        )
        sys.exit(1)


def install_dependencies() -> None:
    step("Installing Python dependencies (openai, google-genai, pillow)")
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade"] + PIP_PACKAGES
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        ok("Dependencies installed")
        return

    # Common failure modes with friendly guidance
    stderr = result.stderr or ""
    print(stderr.strip().splitlines()[-1] if stderr else "")
    if "externally-managed-environment" in stderr:
        warn(
            "Your Python is managed by the system (Homebrew or similar).\n"
            "  Possible solutions:\n"
            f"    • create a venv or use pipx\n"
            f"    • {sys.executable} -m pip install --user " + " ".join(PIP_PACKAGES) + "\n"
            f"    • {sys.executable} -m pip install --break-system-packages " + " ".join(PIP_PACKAGES) + "\n"
            "  Setup will continue — install the packages yourself and re-run if needed."
        )
    else:
        warn("pip install reported an error. Output:")
        print(stderr)
        warn("Setup will continue. Install the packages manually if the skill doesn't work.")


def render_generate_py(openai_key: str, gemini_key: str) -> str:
    """Replace the empty key strings in generate.example.py with real keys."""
    src = TEMPLATE.read_text(encoding="utf-8")

    def safe_replace(text: str, var: str, value: str) -> str:
        # Match: VAR = "anything" (including empty) on a single line; preserve comment tail
        pattern = rf'^({re.escape(var)}\s*=\s*)"[^"]*"'
        # Backslash + double quote do not occur in real OpenAI/Gemini key formats,
        # but we escape for safety.
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        new, n = re.subn(pattern, rf'\1"{escaped}"', text, count=1, flags=re.MULTILINE)
        if n != 1:
            fail(f"Could not find the {var} line in generate.example.py")
            sys.exit(2)
        return new

    src = safe_replace(src, "OPENAI_API_KEY", openai_key)
    src = safe_replace(src, "GEMINI_API_KEY", gemini_key)
    return src


def install_local(generate_py: str, assume_yes: bool) -> None:
    step(f"Local install → {SKILL_INSTALL_DIR}")
    SKILL_INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    target_skill = SKILL_INSTALL_DIR / "SKILL.md"
    target_script = SKILL_INSTALL_DIR / "generate.py"

    if target_script.exists():
        warn(f"{target_script} already exists (may contain your existing keys).")
        if not confirm("Overwrite with new keys?", default=False, assume_yes=assume_yes):
            warn("Skipped local generate.py.")
        else:
            target_script.write_text(generate_py, encoding="utf-8")
            os.chmod(target_script, 0o600)
            ok(f"Wrote {target_script} (mode 600)")
    else:
        target_script.write_text(generate_py, encoding="utf-8")
        os.chmod(target_script, 0o600)
        ok(f"Wrote {target_script} (mode 600)")

    shutil.copyfile(SKILL_MD, target_skill)
    ok(f"Wrote {target_skill}")


def build_bundle(generate_py: str, bundle_path: Path, assume_yes: bool) -> None:
    step(f"Building bundle → {bundle_path}")
    if bundle_path.exists():
        warn(f"{bundle_path} already exists.")
        if not confirm("Overwrite?", default=True, assume_yes=assume_yes):
            warn("Skipped bundle.")
            return

    bundle_path.parent.mkdir(parents=True, exist_ok=True)

    # Bundle structure: image/SKILL.md + image/generate.py (top-level dir 'image')
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "image"
        tmp_path.mkdir()
        shutil.copyfile(SKILL_MD, tmp_path / "SKILL.md")
        (tmp_path / "generate.py").write_text(generate_py, encoding="utf-8")

        with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in tmp_path.iterdir():
                zf.write(f, arcname=f"image/{f.name}")

    os.chmod(bundle_path, 0o600)
    ok(f"Wrote {bundle_path} (mode 600, contains your API keys)")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(
        description="Image Skill setup — installs deps, asks for keys, places the skill and builds an import bundle.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Security: the generated .skill file contains your API keys. Treat it like a password.",
    )
    p.add_argument("--openai-key", help="OpenAI API key (otherwise asked interactively)")
    p.add_argument("--gemini-key", help="Gemini API key (otherwise asked interactively)")
    p.add_argument("--no-deps", action="store_true", help="Skip pip install")
    p.add_argument("--no-local", action="store_true", help="Skip install to ~/.claude/skills/image/")
    p.add_argument("--no-bundle", action="store_true", help="Skip building the .skill bundle")
    p.add_argument(
        "--bundle-path",
        default="image.skill",
        help="Path for the bundle (default: ./image.skill)",
    )
    p.add_argument("-y", "--yes", action="store_true", help="Accept all prompts")
    args = p.parse_args()

    if args.no_local and args.no_bundle:
        fail("Nothing to do: both --no-local and --no-bundle were set.")
        return 1

    print("Image Skill setup")
    print("─" * 60)
    print("This script will:")
    if not args.no_deps:
        print("  • Install Python dependencies (openai, google-genai, pillow)")
    print("  • Ask for your API keys (hidden input, not in shell history)")
    if not args.no_local:
        print(f"  • Place the skill in {SKILL_INSTALL_DIR}")
    if not args.no_bundle:
        print(f"  • Build a bundle → {args.bundle_path}")

    if not confirm("\n  Continue?", default=True, assume_yes=args.yes):
        print("Cancelled.")
        return 0

    check_prerequisites()

    if not args.no_deps:
        install_dependencies()

    step("API keys")
    print("  Input is hidden. Keys are not displayed, not logged, not in shell history.")
    openai_key = args.openai_key or read_key("OpenAI API key (sk-... or sk-proj-...)", ("sk-",))
    gemini_key = args.gemini_key or read_key("Gemini API key (AIza...)", ("AIza",))

    generate_py = render_generate_py(openai_key, gemini_key)

    if not args.no_local:
        install_local(generate_py, args.yes)

    bundle_path = Path(args.bundle_path).expanduser().resolve()
    if not args.no_bundle:
        build_bundle(generate_py, bundle_path, args.yes)

    # Final summary
    print("\n" + "─" * 60)
    print("Done.\n")
    if not args.no_local:
        print(f"  Local install : {SKILL_INSTALL_DIR}")
        print("                  → Claude Code picks up the skill automatically")
    if not args.no_bundle:
        print(f"  Bundle        : {bundle_path}")
        print("                  → Import into claude.ai or Claude desktop:")
        print("                    Settings → Skills → Create / Upload")
        print("                    (extension .skill or .zip — both work)")
    print()
    print("  ⚠ SECURITY")
    print("    The bundle contains your paid API keys. Treat it like a password:")
    print("    • don't commit, don't put in iCloud/Dropbox/Drive")
    print("    • don't forward via mail/Slack without reason")
    print("    • anyone with this file can run API calls on your account")
    print()
    print("  Sandbox note (claude.ai / desktop)")
    print("    Each new session the sandbox reinstalls the Python deps")
    print("    (pip install openai google-genai pillow). The first call takes")
    print("    ~10-20s longer because of this. Normal speed after that.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
