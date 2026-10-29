---
name: parallax-portfolio-checkup
description: 'Individual investor portfolio checkup: health flags, factor scores, redundancy, macro context, and plain-language recommendations. Holdings as [{symbol, weight}].'
inputs:
- name: holdings
  required: true
  description: JSON list of holdings, for example [{"symbol":"AAPL.O","weight":0.30},{"symbol":"MSFT.O","weight":0.25}].
- name: audience
  required: false
  description: audience=client_safe or audience=internal_analyst.
tools:
- get_company_info
- get_peer_snapshot
- check_portfolio_redundancy
- macro_analyst
- list_macro_countries
integration:
  connector: Parallax
  type: mcp
  url: https://mcp.chicago.global/api/mcp
  auth: oauth-user
  requires: Active Parallax subscription (Chicago Global). Without it the skill runs its pre-flight and reports the connector as unavailable; it returns no data.
---

<!-- quick-host-binding:start -->
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
<!-- quick-host-binding:end -->

<!-- white-label: integration-pattern.md -->

# Portfolio Checkup

## When not to use

- Fund manager morning brief → use /parallax-morning-brief
- Client portfolio review (RIA) → use /parallax-client-review
- "Why am I down?" attribution → use /parallax-explain-portfolio
- Trade recommendations → use /parallax-rebalance
- Single stock analysis → use /parallax-should-i-buy
- Portfolio with significant ETF allocation → equity scope only in v1; ETF holdings fail V2 scoring and may silently mismap in V1. A comprehensive proactive ETF health assessment is unsupported here; do not assign equity scores or a full-book health badge to ETFs. Offer /parallax-explain-portfolio only when the user actually asks about a drawdown/return over a period, preserving that concern. Do not invent a loss question to obtain an ETF-aware route.

## Gotchas

- Expected Parallax spend (`_vendored/_parallax/token-costs.md`): `0.15N + 0.1H + 5M` credits for N equity snapshot/identity pairs, H redundancy lookups and M explicit tactical macro markets (0–3); `list_macro_countries` is free. With N=H=10: **7.5 credits at one market, 17.5 at three**. V1 fallback adds 0.1 per successful selected holding; split-and-merge adds the same per-holding rate again for every group call actually made. Each portfolio tool selects at most 100 holdings (quick scores defaults to 50); successful zero-weight lookups still bill. Retry costs and any extra resolution calls are additional.
- JIT-load `_vendored/_parallax/parallax-conventions.md` for §0.0 pre-flight, §1 RIC resolution, §2 identity cross-check, §3 parallel execution, §4 fallbacks, §11 sensitivity, §13 audience mode, §14 host primitives.
- JIT-load `references/health-flags.md` for the 5-flag system, thresholds, the mixed-exchange fallback, and the Verdict-sensitivity wording.
- Per-holding `get_peer_snapshot` + `get_company_info` cross-validation is the primary scoring path; `quick_portfolio_scores` is the V1 fallback with known symbol-mapping bugs for non-US numeric tickers. Never fire it unconditionally.
- JIT-load `_vendored/_parallax/house-view/loader.md` if a view is present: portfolio-level consumer — §3 multipliers on verified-holdings factor aggregates, §4 conflict resolution, §5 rendering, §6 audit. The view biases **Consider** (aligned tilts get implicit support; misaligned holdings get gentle question framing); health flags are unchanged by the view.
- Apply `_vendored/_parallax/white-label/integration-pattern.md` §2 (load), §5 (Branding Header), §7 (About This Report).
- Plain language throughout: "Some holdings could not be verified", never MISMATCH jargon in the body.
- Integration note: production integrations call the tools directly; this markdown report is the interactive/chat tier.

Plain-language portfolio health check with health flags for individual investors.

## Usage

```
/parallax-portfolio-checkup [{"symbol":"AAPL.O","weight":0.30},{"symbol":"MSFT.O","weight":0.25},{"symbol":"VZ.N","weight":0.20},{"symbol":"JNJ.N","weight":0.25}]
/parallax-portfolio-checkup [{"symbol":"AAPL.O","weight":0.30},{"symbol":"MSFT.O","weight":0.25}] audience=client_safe
```

Optional `audience=` argument: `client_safe | internal_analyst`; precedence follows `parallax-conventions.md` §13.1.

## Workflow

Every host interaction below is a host primitive from `parallax-conventions.md` §14 (bindings §14.2, fail-open §14.3). Parallax callables are whatever `discover-tools` returns this session (§0.1).

### Step 0 — Pre-flight

1. Resolve every `_vendored/_parallax/...` and `references/...` path named in this file to the canonical copy (conventions §0.0 item 1).
2. `discover-tools`: bind every logical tool named anywhere in this workflow (Steps 1–2 and the V1 fallback) to the exact callable and schema exposed now.
   <!-- host-note -->
   Claude Code: `ToolSearch` with query `"+Parallax"` before the first Parallax call.
   <!-- /host-note -->
3. Parse args: holdings JSON; optional `audience=`.
4. `load-reference` `_vendored/_parallax/house-view/loader.md`; run §1–§2. If a view is present, capture the load preamble, tilt vector and excludes for Step 4. On §2 failure run without the view.
5. `load-reference` `_vendored/_parallax/white-label/integration-pattern.md`; run §2 and record `white_label_active` + `client_name` (the §2 command prints visual keys only; voice is excluded by design).
6. `load-reference` `references/health-flags.md`.

### Step 1 — Resolve inputs

Before scoring, identify any stated ETF/fund holdings from the supplied identifiers/context; ask about materially ambiguous instrument types instead of guessing. ETF-only proactive health requests receive the explicit equity-scope limitation and stop without equity scoring calls or a health verdict. For mixed books, name excluded ETF/fund holdings and their original weight share; ask whether an equity-sleeve-only check would answer the question before proceeding, retain the full original book for the coverage disclosure and construct a separate equity-only input with weights normalized within that sleeve. Use that explicit sleeve input consistently for scoring, concentration and redundancy, label every result equity-sleeve-only and never imply a complete portfolio health verdict. Do not promise ETF look-through, suitability or a new ETF-health product.

Validate holdings: RIC format (plain tickers → conventions §1), weights summing to ~1.0; fund/OEIC identifiers get the §1 not-covered message and are dropped from scoring with a note.

### Step 2 — Fetch (parallel batches)

**Batch A** — `call-tool` ALL rows in one turn; the per-holding rows fan out N-wide inside the same turn (a sequential per-holding loop is the largest latency leak in this skill):

| Tool | Parameters | Notes |
|---|---|---|
| `get_peer_snapshot` | per holding, all N in parallel | **Primary scoring source** (V2); aggregated client-side |
| `get_company_info` | per holding, all N in parallel | **Ground-truth name oracle** (conventions §2); records `expected_name` |
| `check_portfolio_redundancy` | `holdings` | Overlap detection |
| `list_macro_countries` | — | Market coverage |

`quick_portfolio_scores` is NOT in Batch A; it is the Step 3 V1 fallback only.

**Batch B** — after Step 3 clears the verified set: `macro_analyst` with `component="tactical"` for each unique covered home market derived from the verified holdings' RIC suffixes (cap 3).

### Step 3 — Verify

Gate for Step 4; do not start Batch B or Step 4 before it completes.
1. Cross-validation per conventions §2: `get_peer_snapshot.target_company` vs `get_company_info.name` after normalization; mismatches are excluded from every aggregate and their per-position scores are not displayed.
2. V2 coverage = weight share of holdings that returned a non-empty snapshot AND passed cross-validation.
3. Fallback ladder, first tier whose precondition holds: **V2** (coverage ≥ 50%) → use V2 aggregates, no V1 call; **V1** (coverage < 50%) → `call-tool` `quick_portfolio_scores` once, cross-validate its `holdings_analyzed[].company_name` values against the already-cached `get_company_info` names (never re-fire), and re-derive each mismatched holding's score from its cached `get_peer_snapshot` `comparison[]` row (no new call): the `is_target: true` row when that snapshot passed cross-validation (the endpoint may drop the exchange suffix, e.g. `HPE` for `HPE.N`), otherwise scores unavailable (a snapshot that failed cross-validation is never a score source); **split-and-merge** (V1 coverage also < 50%) → per `references/health-flags.md` "Mixed-Exchange Fallback".
4. `get_company_info` failure after the §0.1 retry: the holding has no oracle → treat as unverified, exclude from aggregates, and name it in the Verification Note as "could not be verified — Parallax company-info lookup failed".

### Step 4 — Compute

Per `references/health-flags.md`, evaluate the 5 flags over the verified set (concentration over the original holdings — it is structural): Low Score (weighted overall ≤ 5.0), Concentration (>15% single / >45% top-3), Redundancy (≥ 2 pairs; low-confidence if coverage < 60%), Value Trap (weighted value ≤ 3.0), Macro Misalignment (overweight in sectors flagged unfavorable in Batch B). Health status: Healthy (0) · Monitor (1–2) · Attention (3+). If a view is active, apply loader.md §3 multipliers (sector × factor) to the verified aggregates before the plain-language mapping; raw per-holding scores stay unchanged.

### Step 5 — Compose

Fill **Output Format** below in order: House View Preamble per loader.md §5.1; Branding Header per integration-pattern.md §5; factor gloss per `parallax-conventions.md` §13.3 by reference; Verdict sensitivity per §11 by reference (internal_analyst only); audience mode per §13; `parallax-conventions.md §9.2` disclosure; disclaimer per loader.md §5 rule 5 when a view is active, otherwise `parallax-conventions.md §9.1`; audit entry per loader.md §6.

### Step 6 — Render (deterministic gate, mandatory)

`write-artifact` the complete drafted report to a new `<draft-path>`, then `run-shell` the shared gate with this skill's key, both per conventions §10.3:

```
python3 "<skill-dir>/_vendored/_parallax/render_gate.py" --skill portfolio-checkup --input "<draft-path>"
```

Write the draft once and never modify it in place, not even to fix one word. If the report needs a change after the draft is written, run the command above on that draft unchanged (ignore that output), then write the corrected report to a fresh path and run the command on it (conventions §10.3).

The entire final message is that command's stdout. The stderr `[render-gate] WARN:` line is diagnostics: never include it. Degraded-state notes go inside their section, never above the report. If `run-shell` is absent, apply conventions §14.3 (render-gate row). No Step 7.

## Output Format

**Begin the response immediately with the rendered report — no preamble.** When no house view and no white-label client are active (the default), the **first line of the output is the Portfolio Health Status header**, in this exact form:

`## Portfolio Health Status: <🟢|🟡|🔴> **<Healthy|Monitor|Attention>** — <N> of 5 flags raised`

(When a house view or white-label client is active, the House View Preamble / Branding Header precede this line per the rules below; the no-preamble rule still applies — those are rendered output, not internal scaffold.)

- **House View Preamble** (only if view active) — render per loader.md §5 rule 1 (banner from Pre-Workflow + low-confidence warnings). Per loader.md §5.1 the preamble goes at the very top — it precedes the Branding Header.
- **Branding Header** (only if `white_label_active` AND `client_name != ""`) — single line immediately below the House View Preamble (or at the very top if no view): `**<client_name>** portfolio checkup`. Logo handling per integration-pattern.md §5: empty path → text only; URL → embed; absolute local (`/` or `~`) → skip embed and append `Logo on file: <basename>` to About This Report.
- **Portfolio Health Status** (Healthy/Monitor/Attention badge with flag count)
- **Verification Note** *(only render if any cross-validation mismatches were detected)* — plain-language note: "Some holdings (X out of N) could not be matched to verified data and were excluded from aggregate factor analysis: [list of symbols]. The remaining N-X holdings drive the scores below."
- **Your Portfolio Scorecard** (simple factor table with plain-language labels; flag indicators per holding. Mismatched holdings show "—" instead of scores.)
- **Health Flags** (each triggered flag explained in plain language — what it means, why it matters)
- **Verdict sensitivity**: the 1-2 nearest-boundary flags and their arithmetic flip condition for moving Health Status to the adjacent tier, per `references/health-flags.md` "Verdict sensitivity" (renders `parallax-conventions.md` §11 by reference; internal_analyst mode only — omitted under `audience=client_safe` per conventions §13.2; the Health Status verdict itself renders in both modes).
- **Overlap Alert** (if redundancy found, explain why; include reliability note if coverage <60%)
- **Macro Context** (2-3 sentences on relevant economic environment — skip if no covered markets)
- **What This Means** (2-3 plain-language paragraphs)
- **Consider** (suggestions prioritized by flag severity, framed as questions not directives; if view active, suggestions reflect view alignment — view-aligned tilts get implicit support, view-misaligned holdings get gentle question framing per loader.md §3-§4)
- **About This Report** (always present): one line stating branding state per integration-pattern.md §7 markdown column (render per table; do not collapse). If a logo was skipped per the Branding Header rule, append `Logo on file: <basename>` as a second About This Report line. Under `audience=client_safe`, append the §13.4 mode line.

Keep tone friendly and educational.

**AI-interaction disclosure (required regardless of view state):** Render `parallax-conventions.md §9.2` immediately above the disclaimer below.

If active view: use the view-aware disclaimer per loader.md §5 rule 5. Otherwise: render the standard disclaimer verbatim from `parallax-conventions.md` §9.1.


## Failure modes

- ETF-only proactive health request: explicit unsupported boundary, no equity-scoring fallback and no fabricated drawdown. Mixed-book equity-sleeve analysis requires the operator’s agreement and a coverage-qualified label.
- V2 coverage below 50%: V1 fallback, then split-and-merge, per Step 3; the path used is stated in the Verification Note.
- `check_portfolio_redundancy` coverage below 60%: Overlap Alert carries the low-confidence note.
- Macro unavailable or no covered market: Macro Context skipped (Output Format), the Macro Misalignment flag is not evaluated and the flag count says so.
- Fewer than 7 holdings: concentration flags are structural (conventions §4); note them without alarm.
- House-view banner states `malformed` / `expired` / `critical`: the banner renders verbatim (conventions §0.3 item 4).
- Host lacks a primitive: conventions §14.3, per primitive.

## Done when

- First line is the Portfolio Health Status header (or the House View Preamble / Branding Header); every Output Format section rendered or marked unavailable with its reason.
- Every excluded holding is named in the Verification Note with its reason; aggregates state the verified weight share they cover.
- When a view is active: the `view_status` banner appears verbatim; Consider reflects view alignment; audit entry appended per loader.md §6 (every consume event).
- The render gate ran and the reply is its stdout (or the §14.3 note is present in About This Report).
- `parallax-conventions.md §9.2` disclosure and the §9.1 or view-aware disclaimer are present; expected spend stated (Gotchas).
