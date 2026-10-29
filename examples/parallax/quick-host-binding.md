## Host binding: Amazon Quick

This block was added when the skill was repackaged for Amazon Quick. It only
binds the host primitives of `_vendored/_parallax/parallax-conventions.md` §14 to
Amazon Quick. It changes no step, gate, formula or output rule below. Where this
block and §14.2 disagree about a host, this block wins for Amazon Quick; every
other rule in the workflow stays as written.

| Primitive | Amazon Quick binding |
|---|---|
| `discover-tools` | The tools of the **Parallax** connector (Customize > Connectors) that are listed in this chat are the discovery result. If no Parallax tool is listed, or a call returns an authentication or subscription error, the Parallax connector is unavailable: apply conventions §0.0 item 4 and §14.3. Never fall back to tool names written in this skill. |
| `call-tool` | Call the listed Parallax tools. Treat parallel calls as *verify*: if they are not issued together, follow the sequential-only row of §14.3. |
| `ask-operator` | Ask in prose in the chat and wait for the user's next message (§14.3). |
| `run-shell` | Absent. Apply the `run-shell` rows of §14.3. |
| `invoke-skill` | Name the other skill in prose. A `/parallax-<name>` usage line in this file means "use the parallax-<name> skill"; if that skill is not installed, route by prose (§14.3). |
| `load-reference` | Read the file from this skill's reference files. Shared files are under `_vendored/_parallax/`. |
| `write-artifact` | Absent. Apply the `write-artifact` row of §14.3. |
| `read-config` | Absent: no environment and no `~/.parallax/` state. Every `PARALLAX_*` switch takes its default; no house view and no white-label branding are active. |
| `fetch-url` | Absent unless the user enabled a web tool in this chat. |
| `schedule-task` | Absent. Do not offer scheduling. |

Inputs in Amazon Quick are given in the chat message, in the same form as the
usage lines below (for example "use parallax-should-i-buy for AAPL").
