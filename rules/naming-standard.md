# Repository Naming Standard

## Prefixes

- `advancerbots-*`: deployable services, contracts, SDKs, and runtime packages used by AdvancerBots.
- `advancersoft-*`: organization tooling, generators, infrastructure, CI utilities, and shared platform assets.

## Deployable service repositories

Use:

`advancerbots-<bounded-context>-<service-kind>`

Examples:

- `advancerbots-auth-api`
- `advancerbots-statistics-api`
- `advancerbots-data-provider`
- `advancerbots-browser-runtime`
- `advancerbots-settings-api`

## Shared repositories

Use:

`advancersoft-<tool-or-platform-area>`

Examples:

- `advancersoft-typescript-generator`
- `advancersoft-infrastructure`
