# claude-skill-to-quick

Convert Claude skills (Claude Code plugins, marketplace bundles, `.skill` uploads)
into skill packages that Amazon Quick can import under **Customize > Skills**.

Amazon Quick does not read `.claude-plugin/marketplace.json`, `plugin.json`,
`.mcp.json` or `install.sh`. It reads one folder (or zip) per skill with a
`SKILL.md` at its root, plus the reference files that skill uses. MCP servers are
added separately as connectors under **Customize > Connectors**.
This repository holds the method and a small converter that does that repackaging
without touching the workflow text.

## What is in here

| Path | What it is |
|---|---|
| `converter/claude2quick.py` | Converter: Claude skill folder or `.skill`/`.zip` in, Quick folder + zip + JSON report out |
| `docs/CONVERSION-GUIDE.md` | The method: how each Claude packaging piece maps to Amazon Quick, and the checks to run |
| `examples/parallax/` | Worked example: two Parallax equity-research workflows converted for Amazon Quick |
| `tests/` | Unit tests for the converter (`python -m unittest discover -s tests`) |

## Quick start

```powershell
pip install pyyaml
python converter/claude2quick.py path/to/my-skill `
    --out dist `
    --profile my-skill.quick.yaml `
    --binding my-host-binding.md
```

Then in Amazon Quick: **Customize > Skills > Create > From file**, pick
`dist/my-skill.zip` (or **From folder**, pick `dist/my-skill/`), choose **Try it**,
then **Publish**.

## What the converter guarantees

* The workflow body of `SKILL.md` is not edited. After conversion it removes the
  inserted host-binding block again and compares SHA-256 of the remaining body with
  the source body. A mismatch fails the run.
* `name` and `description` are copied unchanged. Keys from the profile
  (`inputs`, `tools`, `integration`) are added to the frontmatter.
  `--minimal-frontmatter` writes only `name` and `description`, for use if a Quick
  import ever rejects extra keys.
* Line endings (LF or CRLF) are preserved and checked for mixing.
* Every relative file path that `SKILL.md` mentions (`references/`, `scripts/`,
  `assets/`, `_vendored/`, `_parallax/`) must exist inside the package.
* No symlinks, all text files UTF-8, folder name equals frontmatter `name`
  (lowercase letters, digits, hyphens, max 64), description max 1024 characters.
* Archives with absolute or `..` paths are refused.

## Not verified yet

* The exact frontmatter keys Amazon Quick reads beyond `name` and `description`.
  The AWS user guide describes a skill as description, instructions, referenced
  tools and reference files, and does not publish a frontmatter schema. The first
  import should be followed by **Export** of the imported skill, to see which keys
  Quick kept.
* Whether Amazon Quick runs scripts bundled with a skill. The Parallax example
  treats shell execution as absent and uses the workflow's own documented fallbacks.

## License

MIT, see `LICENSE`. The example under `examples/parallax/quick-skills/` contains
files from [parallax-workflows](https://github.com/bencharoenwong/parallax-workflows)
(MIT, Copyright (c) 2026 Chicago Global Capital Pte Ltd and contributors); its
license is kept as `examples/parallax/quick-skills/UPSTREAM-LICENSE`.
