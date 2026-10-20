# Repository rules

## Local validation gate

- Hosted CI is replaced by `python3 scripts/validate_local.py run`. Preserve all checks in `scripts/local-validation.json`; do not skip failed tests or relax production guards.
- Run on clean committed source before review and again on merged main before release. Verify the exact report using `python3 scripts/validate_local.py verify <report>`. A passed report is required; hosted Actions are not required. Publication/deployment still require existing authorization, source ownership and rollback checks.
