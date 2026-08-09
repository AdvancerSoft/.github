# Branch Protection Standard

Apply to every AdvancerSoft repository.

## `main`

- Require pull request before merging.
- Require at least one approving review.
- Require status checks to pass before merging.
- Require branch to be up to date before merging where supported.
- Block force pushes.
- Block branch deletion.
- Require conversation resolution before merging.
- Do not allow direct commits except emergency repository-owner recovery.

## CI-only phase

Phase 1 repositories must not deploy from GitHub Actions. Workflows may validate formatting, tests, build, repository policy, and generated contract drift only.
