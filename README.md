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
| `examples/aws-agent-plugins/` | Worked example with no login: two awslabs/agent-plugins skills on the public AWS Knowledge MCP Server. Use it to test a conversion end to end |
| `tools/recheck.py` | Re-run the package checks on folders that were already built |
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
* `name` and `description` are copied unchanged, and so are the other open Agent
  Skills keys when present (`license`, `compatibility`, `metadata`). Claude-only keys
  (`allowed-tools`, `argument-hint`, `user-invocable`, ...) are dropped and listed in
  the report. Keys from the profile (`inputs`, `tools`, `integration`) are added.
  `--minimal-frontmatter` writes only `name` and `description`, for use if a Quick
  import ever rejects extra keys.
* Line endings (LF or CRLF) are preserved and checked for mixing.
* Every relative file path that `SKILL.md` mentions (`references/`, `scripts/`,
  `assets/`, `_vendored/`, `_parallax/`) must exist inside the package.
* Every relative markdown link in every `.md` file of the package must resolve
  inside the package. Links in code spans and code blocks are ignored. A link that
  climbs out (`../../scripts/x.sh`) works in a Claude plugin tree but not in Quick;
  it fails the run unless passed with `--allow-missing <target>`, which you should
  do only when the host-binding block tells the model that file is absent.
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

The example under `examples/aws-agent-plugins/quick-skills/` contains files from
[awslabs/agent-plugins](https://github.com/awslabs/agent-plugins), Apache-2.0,
copyright Amazon.com, Inc. or its affiliates. Its license and notice are kept as
`UPSTREAM-LICENSE` and `UPSTREAM-NOTICE` in that folder; the only modified file in
each skill is `SKILL.md` (marked host-binding block and frontmatter).
