# Rebuild the two Parallax skills for Amazon Quick from a pinned upstream commit.
# Usage (PowerShell 7, from the repo root):  pwsh examples/parallax/build.ps1
# Output: examples/parallax/quick-skills/<name>/, <name>.zip, <name>.conversion.json
$ErrorActionPreference = "Stop"

$UpstreamRepo   = "https://github.com/bencharoenwong/parallax-workflows.git"
$UpstreamCommit = "863be9eb954406664745d7f461d6e2752936485d"   # 2026-10-29
$Skills         = @("parallax-should-i-buy", "parallax-portfolio-checkup")

$Here    = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root    = Resolve-Path (Join-Path $Here "..\..")
$Work    = Join-Path ([IO.Path]::GetTempPath()) "parallax-upstream-$UpstreamCommit"
$OutDir  = Join-Path $Here "quick-skills"
$WebOut  = Join-Path $HOME "Downloads\claude-web-skills"   # fixed by upstream build_bundle.py

if (-not (Test-Path $Work)) {
    git clone --quiet $UpstreamRepo $Work
}
git -C $Work fetch --quiet --depth 1 origin $UpstreamCommit
git -C $Work checkout --quiet $UpstreamCommit

# Stage 1: the upstream packager vendors _parallax/ into each skill and rewrites references.
# The upstream leak-scan needs a maintainer-only term list; without it, run with built-in terms.
$env:PARALLAX_ALLOW_PARTIAL_SCAN = "1"
$env:PYTHONUTF8 = "1"
python (Join-Path $Work "skills\_parallax\scripts\build_bundle.py") web @Skills
if ($LASTEXITCODE -ne 0) { throw "upstream build_bundle.py web failed" }

# Stage 2: repackage for Amazon Quick.
New-Item -ItemType Directory -Force $OutDir | Out-Null
$failed = 0
foreach ($s in $Skills) {
    python (Join-Path $Root "converter\claude2quick.py") (Join-Path $WebOut "$s.skill") `
        --out $OutDir `
        --profile (Join-Path $Here "profiles\$s.yaml") `
        --binding (Join-Path $Here "quick-host-binding.md")
    if ($LASTEXITCODE -ne 0) { $failed++ }
}
Copy-Item (Join-Path $Work "LICENSE") (Join-Path $OutDir "UPSTREAM-LICENSE") -Force
Set-Content -Encoding utf8 (Join-Path $OutDir "UPSTREAM-COMMIT") $UpstreamCommit
if ($failed) { throw "$failed skill(s) failed conversion checks" }
