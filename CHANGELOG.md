# Changelog

## 2026-10-20

- Changed: replace automatic hosted CI with reproducible exact-commit local validation and hashed reports; retain migrated build/test/policy commands, isolated test dependencies and linux/amd64 images where applicable.
- Why: account limits must not prevent verification while preserving failed-test and source-revision release gates.
- Affected: `.github/workflows/ci.yml`, `scripts/validate_local.py`, `scripts/local-validation.json`, `tests/test_local_validation.py`, `.gitignore`, `README.md`, `AGENTS.md`, `CHANGELOG.md`.
- Verified: validator regression tests and the local report record actual command exit codes, TRX counters, log hashes and image identity. Runtime code, wire contracts, package versions and production configuration unchanged; no deployment or publication.

