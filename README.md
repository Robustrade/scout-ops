# Scout Ops - Declarative Alert Management

Scout Ops is a framework for managing API alerts as code. Define your APIs and their SLO thresholds in simple YAML files organized by team, and the pipeline takes care of validation, generation, and deployment.

## The Problem

Managing alerts for API endpoints manually doesn't scale. As the number of endpoints grows, keeping alert rules consistent, up-to-date, and properly configured across environments becomes error-prone and time-consuming. Changes require navigating UIs, copy-pasting configurations, and hoping nothing gets missed.

## The Solution

Scout Ops treats alert definitions as code:

- **Team-based YAML specs** define APIs and their SLO thresholds, organized by team
- **A global SLA file** provides default thresholds that teams can override
- **A build pipeline** validates specs, generates alert rules, and deploys them
- **A single global config** controls datasource settings and query templates

## How It Works

```
specs/                              alerts/
  sla.yaml (global defaults)         validate -> build -> render -> deploy
  teams/
    payments/                                    |
      api.yaml    ──────────────>
      sla.yaml    ──────────────>              resources.json -> alerting platform
    integrations/
      api.yaml    ──────────────>
      sla.yaml    ──────────────>
```

1. **Define** team API specs in `specs/teams/<team>/api.yaml` and SLO overrides in `specs/teams/<team>/sla.yaml`
2. **Validate** specs for correctness (required fields, duplicates, format)
3. **Build** JSON inputs by joining APIs with SLAs and resolving fallbacks against `specs/sla.yaml`
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

Define global SLO defaults:

```yaml
# specs/sla.yaml
apis:
  - name: "*"
    slo:
      error_rate:
        threshold: 5
        operator: ">"
        unit: percent
        window: 5m
        alert: true
      latency:
        threshold: 1000
        operator: ">"
        unit: ms
        window: 5m
        alert: true
```

Add a team with an API:

```yaml
# specs/teams/payments/api.yaml
apis:
  - name: v1-payments-initiate-post
    methods:
      - POST
    paths:
      - /v1/payments/initiate
    service:
      name: payment-service
    tags:
      team: payments
      tier: critical
      product: payments
```

Optionally override SLOs for specific APIs:

```yaml
# specs/teams/payments/sla.yaml
apis:
  - name: v1-payments-initiate-post
    slo:
      latency:
        threshold: 800
        operator: ">"
        unit: ms
        window: 5m
        alert: true
```

This generates alert rules like `v1-payments-initiate-post latency above 800ms` and `v1-payments-initiate-post error rate above 5%` (from the global default) -- with queries, labels, annotations, and notification settings all pulled from global config.

## Documentation

| Document | Description |
|---|---|
| [Getting Started](docs/getting-started.md) | Setup, prerequisites, and first deployment |
| [Configuration](docs/configuration.md) | Global config, datasource setup, and workflow configuration |
| [Spec Reference](docs/spec-reference.md) | API spec, SLA spec, and SLA resolution rules |
| [Examples](docs/examples.md) | Common use cases and patterns |

## Powered By

- [Jsonnet](https://jsonnet.org/) — Data templating language
