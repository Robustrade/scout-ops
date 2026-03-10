# Configuration

All pipeline configuration lives in two files inside `alerts/configs/`. SLO thresholds are defined separately in `specs/sla.yaml` and `specs/teams/<team>/sla.yaml`.

## Global Configuration (`alerts/configs/global.yaml`)

This is the central config file for datasource, alerting behavior, and platform settings.

### `envArray`

List of environments to generate alerts for. Each API produces one alert rule per SLO type per environment.

```yaml
envArray:
  - prod
```

To add staging:

```yaml
envArray:
  - prod
  - staging
```

### `alertPlatform`

Platform-level settings for where alerts are stored and how notifications are routed.

```yaml
alertPlatform:
  folderUid: abc123          # Folder UID in the alerting platform
  contactPoint: my-channel   # Default notification channel
  labels: {}                 # Labels applied to every alert rule
```

- `folderUid` — The folder where alert rule groups are created. Must exist before running `make apply`.
- `contactPoint` — The default notification receiver for all alerts.
- `labels` — Key-value pairs added to every alert rule. API tags (team, tier, product) are merged in automatically from the API spec.

### `defaults`

Default values for alert behavior. These control evaluation timing and error handling.

```yaml
defaults:
  alerting:
    pendingPeriod: 2m        # How long condition must hold before firing
    keepFiringFor: ""        # Keep firing after condition clears ("" = disabled)
    noDataState: OK          # What to do when there's no data
    execErrState: Alerting   # What to do on query execution errors
```

> **Note:** SLO thresholds (latency, error rate) are no longer in `global.yaml`. They are defined in `specs/sla.yaml` (global defaults) and optionally overridden in `specs/teams/<team>/sla.yaml`. See [Spec Reference](spec-reference.md) for details.

**Duration format:** `<number><unit>` where unit is `s` (seconds), `m` (minutes), or `h` (hours). Examples: `30s`, `1m`, `5m`, `1h`.

**noDataState options:** `OK`, `NoData`, `Alerting`

**execErrState options:** `OK`, `Alerting`

### `datasource`

Settings for the data source used in alert queries.

```yaml
datasource:
  type: <your-datasource-type>
  uid: <your-datasource-uid>
  database: <your-database>
  table: <your-table>
  dateTimeColDataType: <your-datetime-col-type>
  dateTimeType: <your-datetime-type>
  format: time_series
  queryTemplate: |
    SELECT ...
    FROM {table}
    WHERE ...
    AND path = '{endpoint}'
    AND env = '{env}'
```

- `type` and `uid` — Identify the datasource in the alerting platform.
- `database` and `table` — Database and table names for the query.
- `queryTemplate` — The query template with three placeholders:
  - `{endpoint}` — Replaced with the first path from the API spec (e.g., `/v1/payments/initiate`)
  - `{env}` — Replaced with the environment name (e.g., `prod`)
  - `{table}` — Replaced with the table name

## Jsonnet Defaults (`alerts/configs/alerts.libsonnet`)

This file provides defaults for the Jsonnet template layer. It must match your `global.yaml` datasource settings:

```jsonnet
{
  defaultDataConfig: {
    database: '<your-database>',
    datasource: {
      type: '<your-datasource-type>',
      uid: '<your-datasource-uid>',
    },
  },

  defaultEvalConfig: {
    interval: 60,            // Default evaluation interval in seconds
    pendingPeriod: '5m',
    keepFiringFor: '',
  },

  defaultEvaluator: {
    type: 'gt',              // Greater than
    params: [],
  },

  defaultReducer: {
    type: 'last',            // Use last value
    params: [],
  },

  defaultRelativeTimeRange: {
    from: 300,               // 5 minutes in seconds
    to: 0,
  },
}
```

## GitHub Actions Workflow Configuration

The workflow (`.github/workflows/deploy.yml`) requires these GitHub settings:

### Required Variables and Secrets

| Type | Name | Description |
|---|---|---|
| Variable | `ALERT_PLATFORM_URL` | URL of your alerting platform |
| Secret | `ALERT_PLATFORM_TOKEN` | API token for the alerting platform |
| Variable | `SPECS_REPO` | (Optional) External repo with team specs |
| Secret | `SPECS_REPO_TOKEN` | (Optional) Token for private specs repo access |

### Specs Repo Behavior

1. If `SPECS_REPO` is set, checks out that repo into `specs/`
2. If `SPECS_REPO` is not set, uses local `specs/` directory in this repo
3. If `specs/teams/` doesn't exist, workflow fails immediately

### Workflow Dispatch

The workflow is triggered manually with an `action` input:

- **`diff`** — Validates, generates, and shows what would change
- **`apply`** — Validates, generates, and deploys (only runs on `main` branch)

## Configuration Hierarchy

Values are resolved in this order (later wins):

```
alerts/configs/alerts.libsonnet    (Jsonnet-level defaults)
        |
alerts/configs/global.yaml         (datasource, alerting behavior, platform settings)
        |
specs/sla.yaml                     (global SLO thresholds — wildcard defaults)
        |
specs/teams/<team>/sla.yaml        (team-specific SLO overrides per API)
```

SLO resolution per API:
1. If the API has an entry in the team's `sla.yaml`, use it (per SLO type)
2. For any SLO type not in the team SLA, fall back to the `specs/sla.yaml` wildcard entry

Platform settings (datasource, folder, contact point, alerting behavior) come from `global.yaml` and apply uniformly to all alerts.
