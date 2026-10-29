---
name: deploy
description: 'Deploy applications to AWS. Triggers on phrases like: deploy to AWS, host on AWS, run this on AWS, AWS architecture, estimate AWS cost, generate infrastructure. Analyzes any codebase and deploys to optimal AWS services.'
inputs:
- name: application
  required: true
  description: What the application is, written in the chat (framework, database, traffic, static or dynamic). Quick cannot scan a codebase.
- name: production_ready
  required: false
  description: Say "production-ready" to leave the dev-sized defaults.
- name: region
  required: false
  description: Target AWS Region. The bundled price figures are approximate us-east-1.
tools:
- aws___search_documentation
- aws___read_documentation
- aws___get_regional_availability
integration:
  connector: AWS Knowledge
  type: mcp
  url: https://knowledge-mcp.global.api.aws
  auth: none
  requires: Nothing. Public server, rate limited. The awspricing and awsiac servers of the Claude plugin run locally (uvx) and are not available in Quick.
---

<!-- quick-host-binding:start -->
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
<!-- quick-host-binding:end -->

# Deploy on AWS

Take any application and deploy it to AWS with minimal user decisions.

## Philosophy

**Minimize cognitive burden.** User has code, wants it on AWS. Pick the most
straightforward services. Don't ask questions with obvious answers.

## Workflow

1. **Analyze** - Scan codebase for framework, database, dependencies
2. **Recommend** - Select AWS services, concisely explain rationale
3. **Estimate** - Show monthly cost before proceeding
4. **Generate** - Write IaC code with [security defaults](references/security.md) applied
5. **Deploy** - Run security checks, then execute with user confirmation

## Defaults

See [defaults.md](references/defaults.md) for the complete service selection matrix.

Core principle: Default to **dev-sized** (cost-conscious: small instance sizes, minimal redundancy, and non-HA/single-AZ defaults) unless user says "production-ready".

## MCP Servers

### awsknowledge

Consult for architecture decisions. Use when choosing between AWS services
or validating that a service fits the use case. Helps answer "what's the
right AWS service for X?"

Key topics: `general` for architecture, `amplify_docs` for static sites/SPAs,
`cdk_docs` and `cdk_constructs` for IaC patterns.

### awspricing

Get cost estimates. **Always present costs before generating IaC** so user
can adjust before committing. See [cost-estimation.md](references/cost-estimation.md)
for query patterns.

### awsiac

Consult for IaC best practices. Use when writing CDK/CloudFormation/Terraform
to ensure patterns follow AWS recommendations.

## Principles

- Concisely explain why each service was chosen
- Always show cost estimate before generating code
- Apply [security defaults](references/security.md) automatically (encryption, private subnets, least privilege)
- Run IaC security scans (cfn-nag, checkov) before deployment
- Don't ask "Lambda or Fargate?" - just pick the obvious one
- If genuinely ambiguous, then ask
- **Never recommend AWS App Runner** — it is in maintenance mode. Use ECS Express Mode instead.
- When user explicitly requests a managed application platform or signals low infrastructure involvement, route to Elastic Beanstalk

## References

- [Service defaults](references/defaults.md)
- [Security defaults](references/security.md)
- [Cost estimation patterns](references/cost-estimation.md)
- [Elastic Beanstalk skill](../elastic-beanstalk/SKILL.md)
