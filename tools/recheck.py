"""Re-check already-built Quick skill folders with the current converter checks.

Usage: python tools/recheck.py <quick-skills dir> [<quick-skills dir> ...]
Reads each <name>.conversion.json next to a folder and reuses its accepted list.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "converter"))
import claude2quick as c  # noqa: E402
import yaml  # noqa: E402

bad = 0
for d in map(Path, sys.argv[1:]):
    for skill in sorted(p.parent for p in d.glob("*/SKILL.md")):
        text = (skill / "SKILL.md").read_text(encoding="utf-8")
        _, fm_text, _ = c.split_frontmatter(text)
        fm = yaml.safe_load(fm_text)
        rep = d / f"{skill.name}.conversion.json"
        allowed = []
        if rep.exists():
            allowed = [a.split(": ", 1)[1] for a in
                       json.loads(rep.read_text()).get("accepted_missing_references", [])]
        r = c.check_package(skill, fm, text, allowed)
        print(("OK  " if not r["problems"] else "FAIL") + f" {skill.name}")
        for p in r["problems"]:
            print("   - " + p)
        bad += bool(r["problems"])
sys.exit(1 if bad else 0)
