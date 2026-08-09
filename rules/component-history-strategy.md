# Component History Strategy

Legacy SkyFox remains unchanged while AdvancerSoft repositories are introduced.

## Strategy

- Preserve SkyFox as the legacy operational repository and audit source.
- New AdvancerSoft repositories start with focused history per component.
- When a component is extracted from SkyFox, retain source commit references in migration notes and pull request descriptions.
- Do not rewrite SkyFox history.
- Do not change the SkyFox remote.
- For deployable services, use repository names that match the runtime component boundary.

## Extraction metadata

Each migrated component should include:

- Original SkyFox path.
- Source commit SHA or merge commit SHA.
- Validation performed during extraction.
- Known runtime dependencies.
- Deployment status.
