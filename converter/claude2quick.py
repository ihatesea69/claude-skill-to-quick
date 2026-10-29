#!/usr/bin/env python3
"""Convert a Claude skill package into an Amazon Quick skill package.

Input  : a skill directory that has SKILL.md at its root, or a Claude `.skill`
         / `.zip` file (one top-level folder that holds SKILL.md).
Output : <out>/<name>/            folder with SKILL.md at its root (Quick "From folder")
         <out>/<name>.zip         zip with SKILL.md at the zip root (Quick "From file")
         <out>/<name>.conversion.json   what changed, file hashes, check results

What the converter changes, and nothing else:
  1. The YAML frontmatter. `name` and `description` are copied unchanged; the
     keys from the profile (`inputs`, `tools`, `integration`) are added.
  2. One host-binding block, inserted right after the frontmatter between
     `<!-- quick-host-binding:start -->` and `<!-- quick-host-binding:end -->`.

The workflow body is never edited. The converter proves it: it removes the
inserted block from the output and checks that the remaining body is
byte-identical (SHA-256) to the source body. Line endings (LF or CRLF) are kept.

Stdlib + PyYAML. Python >= 3.9.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml

BLOCK_START = "<!-- quick-host-binding:start -->"
BLOCK_END = "<!-- quick-host-binding:end -->"
NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
DESCRIPTION_MAX = 1024
# Open Agent Skills frontmatter keys that are copied through when the source has them.
KEEP_KEYS = ("license", "compatibility", "metadata")
# Relative paths a SKILL.md points at, in backticks, brackets or parentheses.
REF_RE = re.compile(r"[`(\[]((?:_vendored|_parallax|references|scripts|assets)/[^`)\]\s#]+)")
# Markdown link targets: [text](target). Resolved relative to the file that holds them.
LINK_RE = re.compile(r"\]\(\s*<?([^)\s>#]+)")
# Code is example text, not a link: drop fenced blocks and inline spans before scanning.
CODE_RE = re.compile(r"```.*?```|~~~.*?~~~|`[^`\n]*`", re.S)
EXTERNAL_RE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|\$\{|\{\{)", re.I)
SKIP_PARTS = {"__pycache__", ".git", ".pytest_cache", ".DS_Store"}


class ConversionError(Exception):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def split_frontmatter(text: str) -> tuple[str, str, str]:
    """Return (newline, frontmatter_yaml, body). Body keeps its exact bytes."""
    newline = "\r\n" if "\r\n" in text[:200] else "\n"
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    if not m:
        raise ConversionError("SKILL.md has no YAML frontmatter between --- lines")
    return newline, m.group(1), text[m.end():]


def stage_source(src: Path, tmp: Path) -> Path:
    """Copy or unzip the source into tmp and return the folder that holds SKILL.md."""
    if src.is_dir():
        if not (src / "SKILL.md").is_file():
            raise ConversionError(f"{src} has no SKILL.md at its root")
        dst = tmp / src.name
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(*SKIP_PARTS))
        return dst
    if src.suffix.lower() in {".skill", ".zip"}:
        with zipfile.ZipFile(src) as z:
            for info in z.infolist():
                p = Path(info.filename)
                if p.is_absolute() or ".." in p.parts:
                    raise ConversionError(f"unsafe path in archive: {info.filename}")
            z.extractall(tmp)
        hits = sorted(tmp.rglob("SKILL.md"), key=lambda p: len(p.parts))
        if not hits:
            raise ConversionError(f"{src} contains no SKILL.md")
        return hits[0].parent
    raise ConversionError(f"unsupported source: {src}")


def build_frontmatter(src_fm: dict, profile: dict, minimal: bool) -> tuple[dict, list[str]]:
    """Return (frontmatter, dropped_keys).

    Kept: name, description, and the other open Agent Skills keys (license,
    compatibility, metadata). Dropped and reported: Claude-only keys such as
    allowed-tools, argument-hint, user-invocable, which Quick has no use for.
    """
    name = src_fm.get("name")
    desc = src_fm.get("description")
    if not name or not desc:
        raise ConversionError("source frontmatter needs both name and description")
    out = {"name": name, "description": desc}
    if not minimal:
        for key in KEEP_KEYS:
            if key in src_fm:
                out[key] = src_fm[key]
        for key in ("inputs", "tools", "integration"):
            if profile.get(key):
                out[key] = profile[key]
    dropped = [k for k in src_fm if k not in out]
    return out, dropped


def broken_links(root: Path) -> list[str]:
    """Relative markdown links, in every .md file, that leave the package or point nowhere.

    Returned as '<file>: <target as written>'. A link that climbs out of the skill
    folder (../../scripts/x.sh) works in the Claude plugin tree but not in Quick,
    which only receives this folder.
    """
    root_abs = root.resolve()
    out = []
    for md in sorted(root.rglob("*.md")):
        text = CODE_RE.sub("", md.read_text(encoding="utf-8", errors="replace"))
        for target in sorted(set(LINK_RE.findall(text))):
            if EXTERNAL_RE.match(target):
                continue
            dest = (md.parent / target).resolve()
            inside = dest == root_abs or root_abs in dest.parents
            if not inside or not dest.exists():
                out.append(f"{md.relative_to(root).as_posix()}: {target}")
    return out


def check_package(root: Path, fm: dict, body: str, allow_missing=()) -> dict:
    """Checks that decide whether the package is safe to upload."""
    problems = []
    if not NAME_RE.match(fm["name"]):
        problems.append(f"name '{fm['name']}' is not lowercase-hyphen, max 64 chars")
    if root.name != fm["name"]:
        problems.append(f"folder '{root.name}' differs from frontmatter name '{fm['name']}'")
    if len(fm["description"]) > DESCRIPTION_MAX:
        problems.append(f"description is {len(fm['description'])} chars, max {DESCRIPTION_MAX}")
    missing = []
    for ref in sorted(set(REF_RE.findall(body))):
        clean = ref.rstrip(".,;:")
        if clean.endswith("...") or clean.endswith("/"):
            continue  # prose placeholder such as `_parallax/...`
        if not (root / clean).exists():
            missing.append(f"SKILL.md: {clean}")
    missing = sorted(set(missing) | set(broken_links(root)))
    # A ref is accepted when its target, as written, is listed with --allow-missing:
    # the host-binding block must then tell the model that file is absent in Quick.
    allowed = {a.strip() for a in allow_missing}
    accepted = [m for m in missing if m.split(": ", 1)[1] in allowed]
    missing = [m for m in missing if m not in accepted]
    if missing:
        problems.append("referenced files missing from the package: " + ", ".join(missing))
    links, non_utf8 = [], []
    for p in root.rglob("*"):
        if p.is_symlink():
            links.append(str(p.relative_to(root)))
        elif p.is_file() and p.suffix in {".md", ".py", ".yaml", ".yml", ".json", ".txt"}:
            try:
                p.read_bytes().decode("utf-8")
            except UnicodeDecodeError:
                non_utf8.append(str(p.relative_to(root)))
    if links:
        problems.append("symlinks are not portable: " + ", ".join(links))
    if non_utf8:
        problems.append("text files that are not UTF-8: " + ", ".join(non_utf8))
    return {"problems": problems, "missing_references": missing,
            "accepted_missing_references": accepted}


def convert(src: Path, out: Path, profile_path: Path | None, binding_path: Path | None,
            minimal: bool = False, allow_missing=()) -> dict:
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) if profile_path else {}
    binding = binding_path.read_text(encoding="utf-8") if binding_path else ""
    with tempfile.TemporaryDirectory() as td:
        staged = stage_source(src, Path(td))
        raw = (staged / "SKILL.md").read_bytes()
        text = raw.decode("utf-8")
        nl, fm_text, body = split_frontmatter(text)
        src_fm = yaml.safe_load(fm_text) or {}
        fm, dropped_keys = build_frontmatter(src_fm, profile, minimal)

        fm_yaml = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=10_000).rstrip("\n")
        block = ""
        if binding.strip():
            inner = binding.strip("\n").replace("\r\n", "\n").replace("\n", nl)
            block = f"{BLOCK_START}{nl}{inner}{nl}{BLOCK_END}{nl}{nl}"
        new_text = "---" + nl + fm_yaml.replace("\n", nl) + nl + "---" + nl + nl + block + body.lstrip("\r\n")
        lead = body[: len(body) - len(body.lstrip("\r\n"))]

        dest = out / fm["name"]
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(staged, dest, ignore=shutil.ignore_patterns(*SKIP_PARTS))
        (dest / "SKILL.md").write_bytes(new_text.encode("utf-8"))

    # Proof that the workflow body is unchanged: drop the block, compare bytes.
    _, _, out_body = split_frontmatter(new_text)
    out_body = out_body.lstrip("\r\n")
    if block:
        if not out_body.startswith(block):
            raise ConversionError("host-binding block is not where it was inserted")
        out_body = out_body[len(block):]
    body_ok = sha256(out_body.encode()) == sha256(body.lstrip("\r\n").encode())
    crlf = new_text.count("\r\n")
    lone_lf = new_text.count("\n") - crlf
    line_ending_ok = (lone_lf == 0) if nl == "\r\n" else (crlf == 0)

    checks = check_package(dest, fm, new_text, allow_missing)
    if not body_ok:
        checks["problems"].append("workflow body changed during conversion")
    if not line_ending_ok:
        checks["problems"].append(f"mixed line endings: {crlf} CRLF, {lone_lf} LF")

    zip_path = out / f"{fm['name']}.zip"
    files = sorted(p for p in dest.rglob("*") if p.is_file())
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(dest).as_posix())

    report = {
        "name": fm["name"],
        "source": src.name,  # file name only: reports get committed, local paths must not
        "frontmatter_keys": list(fm),
        "dropped_frontmatter_keys": dropped_keys,
        "host_binding_inserted": bool(block),
        "newline": "CRLF" if nl == "\r\n" else "LF",
        "source_skill_md_sha256": sha256(raw),
        "source_body_sha256": sha256(body.lstrip("\r\n").encode()),
        "body_unchanged": body_ok,
        "leading_blank_lines_dropped": len(lead),
        "file_count": len(files),
        "zip": zip_path.name,
        "zip_bytes": zip_path.stat().st_size,
        "accepted_missing_references": checks["accepted_missing_references"],
        "problems": checks["problems"],
        "ok": not checks["problems"],
    }
    (out / f"{fm['name']}.conversion.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("source", type=Path, help="skill folder, .skill or .zip")
    ap.add_argument("--out", type=Path, default=Path("dist"))
    ap.add_argument("--profile", type=Path, help="YAML with inputs / tools / integration")
    ap.add_argument("--binding", type=Path, help="Markdown host-binding block to insert")
    ap.add_argument("--minimal-frontmatter", action="store_true",
                    help="write only name + description (fallback if Quick rejects extra keys)")
    ap.add_argument("--allow-missing", action="append", default=[], metavar="TARGET",
                    help="link target (as written) that is known to be absent in Quick; "
                         "the binding block must say so. Repeatable.")
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)
    try:
        r = convert(a.source, a.out, a.profile, a.binding, a.minimal_frontmatter,
                    a.allow_missing)
    except ConversionError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    status = "OK" if r["ok"] else "FAIL"
    print(f"{status} {r['name']}: {r['file_count']} files, zip {r['zip_bytes']} bytes, "
          f"body_unchanged={r['body_unchanged']}")
    for p in r["problems"]:
        print(f"  - {p}")
    for p in r["accepted_missing_references"]:
        print(f"  ~ accepted absent in Quick: {p}")
    if r["dropped_frontmatter_keys"]:
        print("  ~ dropped frontmatter keys: " + ", ".join(r["dropped_frontmatter_keys"]))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
