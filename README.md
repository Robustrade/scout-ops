# Scout Ops - Declarative Alert Management

Scout Ops is a framework for managing API endpoint alerts as code. Define your endpoints and their thresholds in simple YAML files, and the pipeline takes care of validation, generation, and deployment.

## The Problem

Managing alerts for API endpoints manually doesn't scale. As the number of endpoints grows, keeping alert rules consistent, up-to-date, and properly configured across environments becomes error-prone and time-consuming. Changes require navigating UIs, copy-pasting configurations, and hoping nothing gets missed.

## The Solution

Scout Ops treats alert definitions as code:

- **YAML specs** define what to monitor and at what thresholds
- **A build pipeline** validates specs, generates alert rules, and deploys them
- **A single global config** controls defaults, datasource settings, and query templates
- **Per-alert overrides** let you customize anything without changing the pipeline

## How It Works

```
specs/                              alerts/
  endpoints/                          validate → build → render → deploy
    users.yaml        ─────────>
    payments.yaml     ─────────>        ↓
    orders.yaml       ─────────>      resources.json → alerting platform
```

1. **Define** endpoint alert specs in `specs/alerts/endpoints/*.yaml`
2. **Validate** specs for correctness (required fields, duplicates, format)
3. **Build** JSON inputs by merging specs with global defaults
4. **Render** Jsonnet templates into deployable alert resources
5. **Deploy** via `grr diff` (preview) or `grr apply` (deploy)

## Quick Start

```bash
cd alerts
make config    # one-time: configure platform credentials
make generate  # validate + build + render
make diff      # preview what would change
make apply     # deploy to alerting platform
```

## Minimal Example

```yaml
# specs/alerts/endpoints/users.yaml
endpoint: /api/v1/users
alerts:
  - type: latency
    threshold_ms: 90
```

This single file generates a complete alert rule with query, threshold, labels, annotations, and notification settings — all pulled from global defaults.

## Documentation

| Document | Description |
|---|---|
| [Getting Started](docs/getting-started.md) | Setup, prerequisites, and first deployment |
| [Configuration](docs/configuration.md) | Global config, datasource setup, and workflow configuration |
| [Spec Reference](docs/spec-reference.md) | Complete YAML spec format and field reference |
| [Examples](docs/examples.md) | Common use cases and patterns |

## Powered By

- [Grafana](https://grafana.com/) — Alerting platform
- [Grizzly](https://github.com/grafana/grizzly) — Infrastructure-as-code for Grafana resources
- [Jsonnet](https://jsonnet.org/) — Data templating language
