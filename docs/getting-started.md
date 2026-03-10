# Getting Started

## Prerequisites

- **jsonnet** — Template rendering engine (`brew install go-jsonnet` on macOS)
- **grr** — CLI tool for deploying alert resources to the alerting platform
- **Python 3** — Runs validation and build scripts
- **Ruby** — Ships with macOS; used for YAML parsing (no pip dependencies needed)

## Initial Setup

### 1. Configure platform credentials

Set your alerting platform URL and API token:

```bash
cd alerts
export ALERT_PLATFORM_URL="https://your-alerting-platform.example.com"
export ALERT_PLATFORM_TOKEN="your-api-token"
make config
```

This creates a deployment context named `scout` with your credentials.

### 2. Update global configuration

Edit `alerts/configs/global.yaml` with your actual values:

```yaml
envArray:
  - prod

alertPlatform:
  folderUid: <your-folder-uid>        # Folder where alerts are stored
  contactPoint: <your-contact-point>  # Default notification channel
  labels: {}

defaults:
  alerting:
    pendingPeriod: 2m
    keepFiringFor: ""
    noDataState: OK
    execErrState: Alerting

datasource:
  type: <your-datasource-type>
  uid: <your-datasource-uid>
  database: <your-database>
  table: <your-table>
  dateTimeColDataType: <your-datetime-col-type>
  dateTimeType: <your-datetime-type>
  format: time_series
  queryTemplate: |
    <your-query-with-placeholders>
```

See [Configuration](configuration.md) for full details on each field.

### 3. Update Jsonnet defaults

Edit `alerts/configs/alerts.libsonnet` to match your datasource:

```jsonnet
{
  defaultDataConfig: {
    database: '<your-database>',
    datasource: {
      type: '<your-datasource-type>',
      uid: '<your-datasource-uid>',
    },
  },
  // ... other defaults
}
```

### 4. Set up global SLO defaults

Edit `specs/sla.yaml` with the default SLO thresholds that apply to all APIs unless overridden by a team:

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

### 5. Create your first team and API spec

Create a team directory under `specs/teams/` with an `api.yaml` file:

```yaml
# specs/teams/my-team/api.yaml
apis:
  - name: v1-my-endpoint-get
    methods:
      - GET
    paths:
      - /v1/my-endpoint
    service:
      name: my-service
    tags:
      team: my-team
      tier: high
      product: my-product
```

Optionally, create `specs/teams/my-team/sla.yaml` to override SLO thresholds for specific APIs:

```yaml
# specs/teams/my-team/sla.yaml
apis:
  - name: v1-my-endpoint-get
    slo:
      latency:
        threshold: 200
        operator: ">"
        unit: ms
        window: 5m
        alert: true
```

If no team `sla.yaml` is provided, the global defaults from `specs/sla.yaml` are used for all APIs in the team.

### 6. Generate and preview

```bash
cd alerts
make generate   # validate + build + render
make diff       # preview changes against live platform
```

### 7. Deploy

```bash
make apply      # deploy alert rules
```

## Pipeline Steps

The `make generate` command runs three steps in order:

```
make validate       Validates global SLA + all team api.yaml/sla.yaml files
      |
make build-inputs   Joins APIs with SLAs, resolves fallbacks -> JSON
      |
make generate       Renders Jsonnet templates -> resources.json
```

Then you use `make diff` or `make apply` to interact with the alerting platform.

## Workflow

The full local workflow:

```bash
cd alerts

# One-time setup
make config

# Development cycle
make validate          # Check specs are valid
make generate          # Full pipeline (validate + build + render)
make diff              # Preview changes
make apply             # Deploy

# Cleanup
make clean             # Remove generated files
```

## What Gets Generated

The pipeline produces `alerts/generated/resources.json` containing AlertRuleGroup resources. For each API and each SLO type where `alert: true`, the pipeline generates an alert rule per environment with:

- A data query (from your query template with endpoint/env/table substituted)
- A reduce step (last value)
- A threshold comparison (based on SLO operator and threshold)
- Labels from API tags, global config, and environment
- Annotations with auto-generated summary and description
- Notification settings

Alert titles follow the format: `<api-name> <slo-type> above <threshold><unit>` (e.g., `v1-payments-initiate-post latency above 800ms`).

## Next Steps

- [Configuration](configuration.md) — Understand and customize global.yaml
- [Spec Reference](spec-reference.md) — Full API spec, SLA spec, and resolution rules
- [Examples](examples.md) — Common patterns and use cases
