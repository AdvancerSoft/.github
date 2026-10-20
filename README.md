# AdvancerSoft Phase 1 GitHub Bootstrap

Local staging repository for the first AdvancerSoft GitHub organization setup.

This repository is not a production source of truth yet. It contains the files and standards to apply after GitHub authentication and organization ownership are available.

## Target organization

- GitHub organization: `AdvancerSoft`
- Organization profile repository: `AdvancerSoft/.github`
- Initial private repositories:
  - `AdvancerSoft/advancerbots-contracts`
  - `AdvancerSoft/advancersoft-typescript-generator`
  - `AdvancerSoft/advancersoft-infrastructure`

## Phase 1 limits

- Do not rename, transfer, or modify `github.com/7sereban7/SkyFox`.
- Do not change the SkyFox `origin` remote.
- Do not push from the dirty SkyFox checkout.
- Do not store production secrets in Git.
- Configure CI-only checks first; no deployment workflows in phase 1.

## Local validation

Automatic GitHub-hosted CI is replaced by `python3 scripts/validate_local.py run` on a clean committed checkout. Python 3.11+, the repository SDK, Docker Buildx and any tools listed in `scripts/local-validation.json` are required. Node workflows require Node 22 (`NODE22_BIN` may point to its bin directory). The configuration preserves every migrated workflow command; Actions checkout/setup/artifact upload are replaced by local prerequisites and saved artifacts. For private packages supply `NuGetPackageSourceCredentials_advancersoft` or use a signed-in `gh` CLI with package access; credentials stay in process environment.

Redis/Postgres dependencies declared in the configuration are isolated disposable Docker containers with random loopback-only ports; the runner removes only the containers it creates. No production service is contacted, deployed or published by the runner.

Reports and logs live in `artifacts/local-validation/<commit>/`. Run `python3 scripts/validate_local.py verify <report>` to verify the exact clean commit/tree, all check exit codes, artifact hashes, zero failed/skipped .NET tests, and linux/amd64 image identity where applicable. Repeat checks on merged main before release. Package publishing and deployment retain their separate authorization and safeguards.
