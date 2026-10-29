# Example: awslabs/agent-plugins (no login needed)

Two skills from [awslabs/agent-plugins](https://github.com/awslabs/agent-plugins)
(Apache-2.0), pinned to commit `fbefb376` (2026-10-09), repackaged for Amazon Quick.
This example exists to test the converter end to end: the only connector it needs is
the public **AWS Knowledge MCP Server**, so Try it returns real data with no
subscription and no sign-in.

| Skill | Upstream path | Files | What it needs in Quick |
|---|---|---|---|
| `dsql` | `plugins/databases-on-aws/skills/dsql` | 72 | AWS Knowledge connector |
| `deploy` | `plugins/deploy-on-aws/skills/deploy` | 4 | AWS Knowledge connector |

What this example exercises that the Parallax example does not:

- **Links that leave the skill folder.** `dsql` links `../../scripts/psql-connect.sh`
  and `deploy` links `../elastic-beanstalk/SKILL.md`. Quick receives only the skill
  folder, so the converter fails on these unless each target is passed with
  `--allow-missing` *and* the binding block tells the model it is absent.
- **Extra open frontmatter keys.** `dsql` has `license` and `metadata`; both are kept.
- **Local (stdio) MCP servers.** The Claude plugin also starts `awspricing`,
  `awsiac` and `aurora-dsql` with `uvx`. Quick connects only to remote MCP servers,
  so the binding block marks them absent and points to the skill's own fallback.

## Build

```powershell
pwsh examples/aws-agent-plugins/build.ps1
python tools/recheck.py examples/aws-agent-plugins/quick-skills
```

Output in `quick-skills/`: a folder and a zip per skill, plus `<name>.conversion.json`
(body hash proof, accepted absent links, dropped keys).

## Set up in Amazon Quick

1. **Customize > Connectors > Add > Model Context Protocol (MCP).**
   Name `AWS Knowledge`, endpoint `https://knowledge-mcp.global.api.aws`,
   authentication **No authentication**. Quick discovers 5 tools
   (`aws___search_documentation`, `aws___read_documentation`, `aws___list_regions`,
   `aws___get_regional_availability`, `aws___retrieve_skill`).
2. **Customize > Skills > Import**, upload `quick-skills/dsql.zip`, then `deploy.zip`.
   Attach the AWS Knowledge connector to each skill if Quick asks for tools.
3. Run the Try it prompts below, then **Publish**.
4. **Export** one imported skill and diff its frontmatter against `quick-skills/<name>/SKILL.md`.
   If Quick dropped or rejected `inputs` / `tools` / `integration`, rebuild with
   `--minimal-frontmatter`.

## Try it prompts and pass criteria

| # | Skill | Prompt | Pass when |
|---|---|---|---|
| 1 | dsql | `What is the maximum number of rows one Aurora DSQL transaction can modify? Verify it.` | Calls an AWS Knowledge tool, answers 3,000 (or the current documented value) with a docs link. |
| 2 | dsql | `Convert this MySQL table to Aurora DSQL: CREATE TABLE orders (id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, FOREIGN KEY (user_id) REFERENCES users(id)) ENGINE=InnoDB;` | Rewrites AUTO_INCREMENT and the foreign key per the skill's references, and does **not** claim it ran the SQL. |
| 3 | dsql | `Connect to my DSQL cluster and list the tables.` | Says there is no cluster connection in Quick and gives the SQL / `psql-connect.sh` command for the user to run. |
| 4 | deploy | `Deploy a Flask app with a PostgreSQL database to AWS, dev-sized, us-east-1.` | Recommends services with a short reason each, shows an approximate monthly cost labelled "not queried" **before** any IaC, never recommends App Runner. |
| 5 | deploy | `Deploy it now.` (after #4) | Lists the scan and deploy commands for the user to run and says they have not been run. |

Prompts 3 and 5 are negative tests: they pass when the skill refuses to pretend.

## License

Upstream is Apache-2.0; `quick-skills/UPSTREAM-LICENSE` is a copy. Each converted
`SKILL.md` carries a marked `Host binding: Amazon Quick` block, which is the change
notice Apache-2.0 section 4(b) asks for. Every other file is byte-identical to upstream.
