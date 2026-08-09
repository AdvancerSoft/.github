# AdvancerSoft

AdvancerSoft hosts the next AdvancerBots platform repositories.

The legacy SkyFox repository remains unchanged and continues to operate independently during migration.

## Repository groups

- `advancerbots-*`: deployable services, service contracts, and runtime packages.
- `advancersoft-*`: shared engineering tools, infrastructure, generators, and platform utilities.

## Operating rules

- `main` is protected.
- Changes go through pull requests.
- CI is required before merge.
- Production secrets are never committed to Git.
- Deployment workflows are added only after the parallel production contour is explicitly ready.
