#!/usr/bin/env python3
"""
Image Skill — setup script.

Installeert dependencies, vraagt API-keys, plaatst de skill in
~/.claude/skills/image/ (voor Claude Code) en bouwt een image.skill bundel
die je in claude.ai / Claude desktop kunt importeren.

Veiligheid: het gegenereerde image.skill bestand bevat je betaalde API-keys.
Behandel het als een wachtwoord — niet committen, niet in iCloud/Dropbox,
niet doorsturen.

Voorbeelden:
  ./setup.py                       # interactief, alles in één keer
  ./setup.py --no-deps             # skip pip install
  ./setup.py --no-local            # alleen bundel, geen ~/.claude/skills install
  ./setup.py --no-bundle           # alleen lokale install
  ./setup.py --bundle-path ~/Desktop/image.skill
  ./setup.py --yes                 # accepteer alle bevestigingen (CI / scripted)
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
# Locatie van de repo (waar dit script staat) en de skill-installatiemap
# ----------------------------------------------------------------------------
REPO_DIR = Path(__file__).resolve().parent
TEMPLATE = REPO_DIR / "generate.example.py"
SKILL_MD = REPO_DIR / "SKILL.md"
SKILL_INSTALL_DIR = Path.home() / ".claude" / "skills" / "image"
PIP_PACKAGES = ["openai", "google-genai", "pillow"]


# ----------------------------------------------------------------------------
# Kleine TUI-helpers (geen externe deps)
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
        if raw in ("y", "yes", "j", "ja"):
            return True
        if raw in ("n", "no", "nee"):
            return False


def read_key(label: str, expect_prefix: tuple[str, ...]) -> str:
    """Vraagt een API-key via getpass (input verborgen, niet in shell-history)."""
    while True:
        key = getpass.getpass(f"  {label}: ").strip()
        if len(key) < 20:
            warn("Lijkt te kort voor een geldige key. Opnieuw.")
            continue
        if not any(key.startswith(p) for p in expect_prefix):
            warn(f"Verwachtte prefix {' of '.join(expect_prefix)}.")
            if not confirm("Toch doorgaan met deze waarde?", default=False, assume_yes=False):
                continue
        return key


# ----------------------------------------------------------------------------
# Stappen
# ----------------------------------------------------------------------------
def check_prerequisites() -> None:
    missing = []
    if not TEMPLATE.exists():
        missing.append(str(TEMPLATE))
    if not SKILL_MD.exists():
        missing.append(str(SKILL_MD))
    if missing:
        fail("Vereiste bestanden niet gevonden:")
        for m in missing:
            print(f"      {m}", file=sys.stderr)
        print(
            "\n  Draai dit script vanuit de geclonede image-skill repo.\n"
            "  (git clone https://github.com/mischacoster/image-skill.git)",
            file=sys.stderr,
        )
        sys.exit(1)


def install_dependencies() -> None:
    step("Python-dependencies installeren (openai, google-genai, pillow)")
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade"] + PIP_PACKAGES
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        ok("Dependencies geïnstalleerd")
        return

    # Veelvoorkomende fail-modes met begrijpelijke uitleg
    stderr = result.stderr or ""
    print(stderr.strip().splitlines()[-1] if stderr else "")
    if "externally-managed-environment" in stderr:
        warn(
            "Je Python is door je systeem gemanaged (Homebrew of vergelijkbaar).\n"
            "  Mogelijke oplossingen:\n"
            f"    • pipx install of een venv aanmaken\n"
            f"    • {sys.executable} -m pip install --user " + " ".join(PIP_PACKAGES) + "\n"
            f"    • {sys.executable} -m pip install --break-system-packages " + " ".join(PIP_PACKAGES) + "\n"
            "  Het setup-script gaat door — installeer de packages zelf en run opnieuw als nodig."
        )
    else:
        warn("pip install gaf een fout. Output:")
        print(stderr)
        warn("Setup gaat door. Installeer de packages handmatig als de skill niet werkt.")


def render_generate_py(openai_key: str, gemini_key: str) -> str:
    """Vervang in generate.example.py de lege key-strings door echte keys."""
    src = TEMPLATE.read_text(encoding="utf-8")

    def safe_replace(text: str, var: str, value: str) -> str:
        # Match: VAR = "anything" (inclusief leeg) op één regel; behoud comment-staart
        pattern = rf'^({re.escape(var)}\s*=\s*)"[^"]*"'
        # Backslash + dubbele quote in keys komt niet voor (OpenAI/Gemini formats),
        # maar we escapen voor de zekerheid.
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        new, n = re.subn(pattern, rf'\1"{escaped}"', text, count=1, flags=re.MULTILINE)
        if n != 1:
            fail(f"Kon de regel met {var} niet vinden in generate.example.py")
            sys.exit(2)
        return new

    src = safe_replace(src, "OPENAI_API_KEY", openai_key)
    src = safe_replace(src, "GEMINI_API_KEY", gemini_key)
    return src


def install_local(generate_py: str, assume_yes: bool) -> None:
    step(f"Lokale install → {SKILL_INSTALL_DIR}")
    SKILL_INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    target_skill = SKILL_INSTALL_DIR / "SKILL.md"
    target_script = SKILL_INSTALL_DIR / "generate.py"

    if target_script.exists():
        warn(f"{target_script} bestaat al (bevat mogelijk jouw bestaande keys).")
        if not confirm("Overschrijven met nieuwe keys?", default=False, assume_yes=assume_yes):
            warn("Lokale generate.py overgeslagen.")
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
    step(f"Bundel bouwen → {bundle_path}")
    if bundle_path.exists():
        warn(f"{bundle_path} bestaat al.")
        if not confirm("Overschrijven?", default=True, assume_yes=assume_yes):
            warn("Bundel overgeslagen.")
            return

    bundle_path.parent.mkdir(parents=True, exist_ok=True)

    # Bundel-structuur: image/SKILL.md + image/generate.py (top-level map 'image')
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "image"
        tmp_path.mkdir()
        shutil.copyfile(SKILL_MD, tmp_path / "SKILL.md")
        (tmp_path / "generate.py").write_text(generate_py, encoding="utf-8")

        with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in tmp_path.iterdir():
                zf.write(f, arcname=f"image/{f.name}")

    os.chmod(bundle_path, 0o600)
    ok(f"Wrote {bundle_path} (mode 600, bevat je API-keys)")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main() -> int:
    p = argparse.ArgumentParser(
        description="Image Skill setup — installeert deps, vraagt keys, plaatst de skill en bouwt een import-bundel.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Veiligheid: het gegenereerde .skill bestand bevat je API-keys. Behandel het als wachtwoord.",
    )
    p.add_argument("--openai-key", help="OpenAI API key (anders interactief gevraagd)")
    p.add_argument("--gemini-key", help="Gemini API key (anders interactief gevraagd)")
    p.add_argument("--no-deps", action="store_true", help="Skip pip install")
    p.add_argument("--no-local", action="store_true", help="Skip install naar ~/.claude/skills/image/")
    p.add_argument("--no-bundle", action="store_true", help="Skip bouwen van .skill bundel")
    p.add_argument(
        "--bundle-path",
        default="image.skill",
        help="Pad voor de bundel (default: ./image.skill)",
    )
    p.add_argument("-y", "--yes", action="store_true", help="Accepteer alle bevestigingen")
    args = p.parse_args()

    if args.no_local and args.no_bundle:
        fail("Niks te doen: zowel --no-local als --no-bundle gezet.")
        return 1

    print("Image Skill setup")
    print("─" * 60)
    print("Dit script gaat:")
    if not args.no_deps:
        print("  • Python-dependencies installeren (openai, google-genai, pillow)")
    print("  • Je API-keys vragen (verborgen invoer, niet in shell-history)")
    if not args.no_local:
        print(f"  • De skill plaatsen in {SKILL_INSTALL_DIR}")
    if not args.no_bundle:
        print(f"  • Een bundel bouwen → {args.bundle_path}")

    if not confirm("\n  Doorgaan?", default=True, assume_yes=args.yes):
        print("Geannuleerd.")
        return 0

    check_prerequisites()

    if not args.no_deps:
        install_dependencies()

    step("API-keys")
    print("  Invoer is verborgen. Keys worden niet getoond, niet gelogd, niet in shell-history.")
    openai_key = args.openai_key or read_key("OpenAI API key (sk-... of sk-proj-...)", ("sk-",))
    gemini_key = args.gemini_key or read_key("Gemini API key (AIza...)", ("AIza",))

    generate_py = render_generate_py(openai_key, gemini_key)

    if not args.no_local:
        install_local(generate_py, args.yes)

    bundle_path = Path(args.bundle_path).expanduser().resolve()
    if not args.no_bundle:
        build_bundle(generate_py, bundle_path, args.yes)

    # Slotsamenvatting
    print("\n" + "─" * 60)
    print("Klaar.\n")
    if not args.no_local:
        print(f"  Lokale install : {SKILL_INSTALL_DIR}")
        print("                   → Claude Code pikt de skill automatisch op")
    if not args.no_bundle:
        print(f"  Bundel         : {bundle_path}")
        print("                   → Importeer in claude.ai of Claude desktop:")
        print("                     Settings → Skills → Create / Upload")
        print("                     (extensie .skill of .zip — beide werken)")
    print()
    print("  ⚠ SECURITY")
    print("    De bundel bevat je betaalde API-keys. Behandel als wachtwoord:")
    print("    • niet committen, niet in iCloud/Dropbox/Drive zetten")
    print("    • niet via mail/Slack zonder reden doorsturen")
    print("    • iedereen met dit bestand kan API-calls op jouw rekening doen")
    print()
    print("  Sandbox-noot (claude.ai / Cowork)")
    print("    Bij elke nieuwe sessie installeert de sandbox de Python-deps")
    print("    opnieuw (pip install openai google-genai pillow). Eerste call")
    print("    duurt daardoor ~10-20s extra. Daarna normaal tempo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
