## Host binding: Amazon Quick

This block was added when the skill was repackaged for Amazon Quick. It says
which of the hosts and tools named below exist in Amazon Quick. It changes no
principle, default or step order below.

| Named below | Amazon Quick binding |
|---|---|
| **Analyze** (scan codebase) | Quick has no access to the user's code. Analyze the application description given in the chat. If framework or database is missing and the choice is genuinely ambiguous, ask (per Principles). |
| `awsknowledge` MCP | The **AWS Knowledge** connector (Customize > Connectors, no authentication): `aws___search_documentation`, `aws___read_documentation`, and `aws___get_regional_availability` to confirm a service exists in the target Region. |
| `awspricing` MCP | Absent (it runs locally in the Claude plugin). For **Estimate**, use the approximate figures in `references/cost-estimation.md`, label them "approximate, us-east-1, not queried", and still show them before any IaC. |
| `awsiac` MCP | Absent. Use the AWS Knowledge tools with the `cdk_docs` / `cdk_constructs` topics for IaC patterns. |
| **Generate** | Write the IaC in the chat with `references/security.md` applied. |
| **Deploy**, cfn-nag, checkov | Absent. Quick cannot run commands or reach the user's AWS account. List the security scan and deploy commands for the user to run, and say they have not been run. |
| `../elastic-beanstalk/SKILL.md` | Not in this package. When the routing rule points to Elastic Beanstalk, recommend it in prose and use the Elastic Beanstalk figures in `references/cost-estimation.md`. |
