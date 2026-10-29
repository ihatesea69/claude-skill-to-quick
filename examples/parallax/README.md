# Example: Parallax workflows for Amazon Quick

Source: [bencharoenwong/parallax-workflows](https://github.com/bencharoenwong/parallax-workflows),
commit `863be9eb954406664745d7f461d6e2752936485d` (2026-10-29), MIT.

| Skill | What it does | Input |
|---|---|---|
| `parallax-should-i-buy` | Plain-language evaluation of one stock: factor scores, financial health, macro context, dividends, news, analyst outlook | Ticker or RIC, optional language / register / audience |
| `parallax-portfolio-checkup` | Portfolio health flags, factor scores, redundancy, macro context | Holdings as JSON `[{symbol, weight}]`, optional audience |

Both need the Parallax MCP connector (`https://mcp.chicago.global/api/mcp`) and an
active Parallax subscription to return data. Without a subscription they only show
that the packaging works and report the connector as unavailable.

## Rebuild

```powershell
pwsh examples/parallax/build.ps1
```

Two stages:

1. Upstream `build_bundle.py web` vendors the shared `_parallax/` files into each
   skill under `_vendored/_parallax/` and rewrites the paths (22 shared and 2
   cross-skill files per skill).
2. `converter/claude2quick.py` adds the Quick frontmatter from `profiles/` and the
   host-binding block `quick-host-binding.md`.

## Measured result (2026-10-29)

| Check | parallax-should-i-buy | parallax-portfolio-checkup |
|---|---|---|
| Files in package (upstream / converted) | 25 / 25 | 25 / 25 |
| Files whose hash differs from upstream | only `SKILL.md` | only `SKILL.md` |
| `git diff` of `SKILL.md` | frontmatter + inserted block only | frontmatter + inserted block only |
| `name`, `description` equal to upstream | yes | yes |
| Workflow body SHA-256 unchanged | yes | yes |
| Missing referenced files | 0 | 0 |

## Parallax connector facts

Measured with unauthenticated discovery requests on 2026-10-29:

* `POST /api/mcp` returns 401.
* `/.well-known/oauth-authorization-server` publishes a `registration_endpoint`
  (Dynamic Client Registration), `grant_types_supported: [authorization_code]`,
  `token_endpoint_auth_methods_supported: [none]`, PKCE `S256`, scope `mcp:tools`.

So in Amazon Quick choose **User authentication**; Quick registers itself and each
user signs in with their own Parallax account. There is no service-to-service option.

## Known limits

* `translate-vietnamese-finance` is marked "Held: native review pending" upstream
  and is not included; Vietnamese output (`vi-VN`) is therefore not a released
  Parallax feature.
* House view, white-label branding and the render gate need a shell or local state.
  The host-binding block declares them absent in Amazon Quick, so the workflows
  follow their own documented fallbacks (conventions §14.3).
