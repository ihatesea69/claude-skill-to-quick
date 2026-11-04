# Install a Claude skill into Amazon Quick (playbook for the Quick agent)

This file is written for the Amazon Quick agent. A person pastes two links into
Quick chat: this repository, and the Claude skill repository to install. Follow the
steps below. Reply in the language the person writes in.

## Inputs

* `CONVERTER_REPO`: this repository, https://github.com/ihatesea69/claude-skill-to-quick
* `SOURCE_REPO`: the Claude skill repository the person pasted

If the person gave only one link, ask for the other. Do not guess a repository.

## Rules

1. Never edit the workflow text of a skill. Only packaging changes (frontmatter, a
   host-binding note, vendored shared files). The method and checks are in
   `docs/CONVERSION-GUIDE.md` in `CONVERTER_REPO`; read it first.
2. Never invent data. If a required connector is missing or not signed in, say so and
   stop. Do not answer from memory in place of the connector.
3. Do not ask for, or accept, passwords or API keys in chat. Sign-in happens on the
   provider's own login page.
4. Say plainly which steps you did and which steps the person must do in the Quick UI.

## Step 1. Pick the skills

List the skills in `SOURCE_REPO` (each folder with a `SKILL.md`). If the repo has many,
show the names and descriptions and ask which to install. Do not install all of them
unasked.

## Step 2. Get a Quick-ready package

Check `examples/` in `CONVERTER_REPO` first. If the skill is already built there, use
that package and skip conversion:

| Skill | Package (download) |
|---|---|
| parallax-should-i-buy | https://github.com/ihatesea69/claude-skill-to-quick/raw/main/examples/parallax/quick-skills/parallax-should-i-buy.zip |
| parallax-portfolio-checkup | https://github.com/ihatesea69/claude-skill-to-quick/raw/main/examples/parallax/quick-skills/parallax-portfolio-checkup.zip |

Otherwise convert it. If you can run code, run
`python converter/claude2quick.py <skill folder> --out dist` from `CONVERTER_REPO`
(needs `pyyaml`) and use the zip it writes. If you cannot run code, follow
`docs/CONVERSION-GUIDE.md` by hand, and tell the person the result was not checked by
the converter.

## Step 3. Create the skill in Quick

Create the skill from the package (Customize > Skills > Create > From file, pick the
zip). If you cannot import a file yourself, give the person the download link and the
click path above. After import, choose Try it, and only then Publish.

## Step 4. Connect the tools the skill needs

Find the MCP server the skill uses (`.mcp.json`, the README, or the host-binding note
at the top of the converted `SKILL.md`). Adding a connector is done by the person in
Customize > Connectors. Give them the exact values:

* Parallax: endpoint `https://mcp.chicago.global/api/mcp`, authentication
  **User authentication**, leave Client ID and Client Secret empty. Each user signs in
  with their own Parallax account, and a paid Parallax subscription is required.
* Another server: ask the person for its endpoint, or read it from the repo. Pick
  **No authentication** only if the server answers a `tools/list` request without a
  token. If it answers 401 and publishes OAuth metadata, pick **User authentication**.

## Step 5. Ask for what is missing

End with a short list of what is still needed from the person, for example: sign in to
the connector, confirm they have a subscription, or choose which workflows to keep.
If the connector is not signed in, run Try it anyway and report what the skill says.
For Parallax without a subscription, the expected result is: the skill loads, reports
that it cannot reach Parallax data, and stops without producing any number.

## Report

Finish with three lines: installed skills, connector status, what the person must still
do.
