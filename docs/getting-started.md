# Getting Started

## Prerequisites

- **jsonnet** — Template rendering engine (`brew install go-jsonnet` on macOS)
- **grr** — CLI tool for deploying alert resources
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

This creates a `grr` context named `scout` with your credentials.

### 2. Update global configuration

Edit `alerts/configs/global.yaml` with your actual values:

```yaml
envArray:
  - prod

alertPlatform:
  folderUid: <your-folder-uid>        # Folder where alerts are stored
  contactPoint: <your-contact-point>  # Default notification channel
  labels:
    team: <your-team>

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

### 4. Create your first endpoint spec

```yaml
# specs/alerts/endpoints/my-api.yaml
endpoint: /api/v1/my-endpoint
alerts:
  - type: latency
    threshold_ms: 100
```

### 5. Generate and preview

```bash
cd alerts
make generate   # validate + build + render
make diff       # preview changes against live platform
```

### 6. Deploy

```bash
make apply      # deploy alert rules
```

## Pipeline Steps

The `make generate` command runs three steps in order:

```
make validate       Checks all YAML specs for correctness
      ↓
make build-inputs   Converts YAML specs + global config → JSON
      ↓
make generate       Renders Jsonnet templates → resources.json
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
make generate          # Full pipeline
make diff              # Preview changes
make apply             # Deploy

# Cleanup
make clean             # Remove generated files
```

## What Gets Generated

The pipeline produces `alerts/generated/resources.json` containing AlertRuleGroup resources. Each group contains one or more alert rules, each with:

- A data query (from your query template with endpoint/env/table substituted)
- A reduce step (last value)
- A threshold comparison (greater than your threshold_ms)
- Labels, annotations, and notification settings

## Next Steps

- [Configuration](configuration.md) — Understand and customize global.yaml
- [Spec Reference](spec-reference.md) — Full YAML spec format
- [Examples](examples.md) — Common patterns and use cases
