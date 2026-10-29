# Conversion guide: Claude skills to Amazon Quick

## 1. Map each Claude packaging piece

| Claude piece | What it does in Claude | Amazon Quick equivalent |
|---|---|---|
| `.claude-plugin/marketplace.json` | Lists plugins in a marketplace | None. Share the skill inside Quick (Share / Share with all) |
| `plugin/.claude-plugin/plugin.json` | Plugin name, version, author | None. Keep version in the repo; Quick has Draft and Published versions |
| `plugin/.mcp.json` | Declares MCP servers bundled with the plugin | **Customize > Connectors**, one Model Context Protocol connector per server |
| `install.sh` / `~/.claude/skills` | Copies skills to the local skill directory | **Customize > Skills > Create > From file / From folder** |
| `skills/<name>/SKILL.md` | Entry point of one workflow | Same file, at the root of the Quick skill folder or zip |
| Shared folders via `../_shared/` or symlink | Files used by several skills | Copy ("vendor") into each skill; a Quick skill is self-contained |
| `references/`, scripts, assets | Loaded on demand | Reference files inside the same skill folder |
| `/skill-name args` slash command | Explicit invocation | Name the skill in the chat message, or **Try it** |
| Host tools (`ToolSearch`, `AskUserQuestion`, `Bash`, `Write`, `WebFetch`) | Claude Code tools | Not available by those names; bind them in a host-binding block |

## 2. Steps

1. **Read the source.** List the skills, their shared dependencies, the MCP servers
   in `.mcp.json`, and every host tool a `SKILL.md` names. Check the license file.
2. **Make each skill self-contained.** If the source repo has a packager for
   single-skill uploads (for example a claude.ai `.skill` build), use it: it already
   vendors shared files and rewrites paths. Otherwise copy shared files into the
   skill and fix the relative paths.
3. **Write a profile** (`<skill>.quick.yaml`) with `inputs`, `tools` and
   `integration`, taking every value from the source `SKILL.md`. Do not invent tools
   or inputs.
4. **Write a host-binding block** that says what each host-specific action means in
   Amazon Quick and what to do when it is not available. Keep it to binding only:
   no new steps, no changed rules.
5. **Run the converter** and read the JSON report. `ok` must be `true` and
   `body_unchanged` must be `true`.
6. **Verify independently**, with a different tool than the one that produced the
   files: compare file hashes between source and output (only `SKILL.md` may
   differ) and `git diff --no-index` the two `SKILL.md` files (only the frontmatter
   and the inserted block may change).
7. **Create the connector** in **Customize > Connectors**. Check the server's OAuth
   metadata first:
   `GET <server-root>/.well-known/oauth-protected-resource` and
   `GET <server-root>/.well-known/oauth-authorization-server`.
   A `registration_endpoint` means Amazon Quick can register itself (Dynamic Client
   Registration); choose **User authentication**. Only `authorization_code` in
   `grant_types_supported` means each user signs in with their own account and
   service-to-service authentication will not work.
8. **Import, test, publish.** **Create > From file**, choose **Try it**, then
   **Publish**, then **Share**.
9. **Export once** after the first import and compare the exported frontmatter with
   what you uploaded. Keys that Quick dropped are keys it does not read.

## 3. Define "test passed" before testing

If the data service needs a paid subscription that you do not have, Try it can
only prove the packaging, not the data. Agree in advance on what passes:

* the skill activates (by name and by a matching request);
* it reads its reference files;
* it finds the connector, or reports clearly that the connector is unavailable;
* it does **not** produce numbers, scores or tool names on its own.

A run that invents data without a working connector is a failure, even if the
output looks good.
