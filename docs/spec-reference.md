# Spec Reference

Endpoint alert specs live in `specs/alerts/endpoints/` as YAML files. Each file defines alerts for one API endpoint.

## File Location

```
specs/
  alerts/
    endpoints/
      users.yaml
      payments.yaml
      orders.yaml
```

Each `.yaml` or `.yml` file in this directory is automatically picked up by the pipeline.

## Format

```yaml
endpoint: /api/v1/users
alerts:
  - type: latency
    threshold_ms: 90
```

## Top-Level Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `endpoint` | yes | string | API path. Must start with `/`. Must be unique across all spec files. |
| `alerts` | yes | list | One or more alert definitions for this endpoint. |

## Alert Fields

| Field | Required | Type | Default | Description |
|---|---|---|---|---|
| `type` | yes | string | — | Alert type. Currently only `latency` is supported. |
| `threshold_ms` | yes | number | — | Threshold value in milliseconds. Must be > 0. |
| `severity` | no | string | `warning` | Severity label for the alert rule. |
| `eval_interval` | no | string | `1m` | How often the alert condition is evaluated. |
| `lookback` | no | string | `5m` | Time range the query looks back. |
| `pendingPeriod` | no | string | `2m` | How long the condition must hold before the alert fires. |
| `keepFiringFor` | no | string | `""` | Keep the alert firing after the condition clears. Empty string disables this. |
| `noDataState` | no | string | `OK` | Behavior when the query returns no data. Options: `OK`, `NoData`, `Alerting`. |
| `execErrState` | no | string | `Alerting` | Behavior when the query fails. Options: `OK`, `Alerting`. |
| `labels` | no | object | `{}` | Additional key-value labels. Merged with global labels. |
| `table` | no | string | from global config | Override the datasource table for this alert. |
| `folderUid` | no | string | from global config | Override the alert folder for this alert. |
| `contactPoint` | no | string | from global config | Override the notification channel for this alert. |
| `query_template` | no | string | from global config | Override the entire query template for this alert. |

## Duration Format

Duration fields (`eval_interval`, `lookback`, `pendingPeriod`, `keepFiringFor`) use the format `<number><unit>`:

| Unit | Meaning | Example |
|---|---|---|
| `s` | seconds | `30s` |
| `m` | minutes | `5m` |
| `h` | hours | `1h` |

## Validation Rules

The pipeline validates every spec file before building. These checks are enforced:

1. **Required fields** — `endpoint`, `alerts`, `type`, and `threshold_ms` must be present.
2. **Endpoint format** — Must start with `/`.
3. **No duplicates** — The same endpoint path cannot appear in multiple files.
4. **Alert type** — Must be `latency` (only supported type in v1).
5. **Threshold** — Must be a positive number.
6. **Duration format** — Optional duration fields must match `<number><s|m|h>`.
7. **Non-empty alerts** — The `alerts` list must contain at least one entry.

If any check fails, the pipeline exits with an error before generating anything.

## Generated Output

For each alert in each environment, the pipeline generates:

- **Title:** `High Latency {endpoint} ({env})`
- **Labels:** Global labels + `env`, `endpoint`, `severity`, `alert_type` + any per-alert labels
- **Annotations:** Auto-generated summary and description
- **Query:** The query template with `{endpoint}`, `{env}`, `{table}` substituted
- **Condition:** 3-step evaluation (query → reduce → threshold comparison)

## Alert Grouping

Alerts are grouped by `(environment, eval_interval)`. The group name follows the pattern:

```
endpoint-latency-{env}-{interval_seconds}s
```

For example, with default `eval_interval: 1m`:
- Group name: `endpoint-latency-prod-60s`

Alerts with different `eval_interval` values end up in different groups.
