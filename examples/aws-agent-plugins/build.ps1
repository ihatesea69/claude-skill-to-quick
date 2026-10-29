# Rebuild the two awslabs/agent-plugins skills for Amazon Quick from a pinned upstream commit.
# Usage (PowerShell 7, from the repo root):  pwsh examples/aws-agent-plugins/build.ps1
# Output: examples/aws-agent-plugins/quick-skills/<name>/, <name>.zip, <name>.conversion.json
$ErrorActionPreference = "Stop"

$UpstreamRepo   = "https://github.com/awslabs/agent-plugins.git"
$UpstreamCommit = "fbefb3764e67558fe10ac834dd85db49734aa9b6"   # 2026-10-09

# Skill folder in the plugin tree, and the links that point outside it.
# Every target listed here is named in that skill's binding block as absent in Quick.
$Skills = [ordered]@{
    "dsql" = @{
        Path    = "plugins/databases-on-aws/skills/dsql"
        Missing = @(
            "../../scripts/", "../../scripts/psql-connect.sh", "../../scripts/README.md",
            "scripts/psql-connect.sh", "scripts/README.md",
            "../../../../.mcp.json", "../../../../scripts/loader.sh",
            "../../../../scripts/psql-connect.sh", "../../../../scripts/README.md"
        )
    }
    "deploy" = @{
        Path    = "plugins/deploy-on-aws/skills/deploy"
        Missing = @("../elastic-beanstalk/SKILL.md")
    }
}

$Here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root   = Resolve-Path (Join-Path $Here "..\..")
# core.autocrlf=false: keep upstream bytes as committed, so "byte-identical to upstream"
# holds against the upstream repo and not only against a Windows checkout.
$Work   = Join-Path ([IO.Path]::GetTempPath()) "agent-plugins-$UpstreamCommit-raw"
$OutDir = Join-Path $Here "quick-skills"

if (-not (Test-Path $Work)) {
    git -c core.autocrlf=false clone --quiet --filter=blob:none --no-checkout $UpstreamRepo $Work
    git -C $Work config core.autocrlf false
}
git -C $Work fetch --quiet --depth 1 origin $UpstreamCommit
git -C $Work checkout --quiet $UpstreamCommit

$env:PYTHONUTF8 = "1"
New-Item -ItemType Directory -Force $OutDir | Out-Null
$failed = 0
foreach ($name in $Skills.Keys) {
    $s = $Skills[$name]
    $allow = foreach ($m in $s.Missing) { "--allow-missing"; $m }
    python (Join-Path $Root "converter\claude2quick.py") (Join-Path $Work $s.Path) `
        --out $OutDir `
        --profile (Join-Path $Here "profiles\$name.yaml") `
        --binding (Join-Path $Here "bindings\$name.md") `
        @allow
    if ($LASTEXITCODE -ne 0) { $failed++ }
}
Copy-Item (Join-Path $Work "LICENSE") (Join-Path $OutDir "UPSTREAM-LICENSE") -Force
if (Test-Path (Join-Path $Work "NOTICE")) {
    Copy-Item (Join-Path $Work "NOTICE") (Join-Path $OutDir "UPSTREAM-NOTICE") -Force
}
Set-Content -Encoding utf8 (Join-Path $OutDir "UPSTREAM-COMMIT") $UpstreamCommit
if ($failed) { throw "$failed skill(s) failed conversion checks" }
