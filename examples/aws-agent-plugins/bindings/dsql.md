## Host binding: Amazon Quick

This block was added when the skill was repackaged for Amazon Quick. It says
which of the hosts and tools named below exist in Amazon Quick. It changes no
rule, limit, workflow or example below.

| Named below | Amazon Quick binding |
|---|---|
| `awsknowledge` MCP | The **AWS Knowledge** connector (Customize > Connectors, no authentication). Use its `aws___search_documentation` and `aws___read_documentation` tools for every "verify" query in the limits table. If the connector is not listed in this chat, apply the skill's own **Fallback** rule. |
| `aurora-dsql` MCP (`readonly_query`, `transact`, `get_schema`) | Absent. Quick has no connection to a DSQL cluster. Never claim a query or DDL was executed. Write the SQL for the user to run. |
| `dsql_lint` | Absent. Check SQL against `references/dsql-lint.md` by reading it, and say the SQL was reviewed, not machine-linted. |
| `dsql_search_documentation`, `dsql_read_documentation`, `dsql_recommend` | Absent. Use the AWS Knowledge tools above with DSQL search terms. |
| CloudWatch MCP (Workflow 12) | Absent. Explain the diagnosis steps and the queries; the user runs them. |
| `scripts/` (`psql-connect.sh`, `loader.sh`, cluster scripts, `scripts/README.md`) and `.mcp.json` | Not in this package; they belong to the Claude plugin. Give the command line as written in this skill for the user to run in their own terminal. Never claim it ran. |
| `mcp/platforms/*.md` | Setup notes for other hosts. Ignore them in Quick. |
