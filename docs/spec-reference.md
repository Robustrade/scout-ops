# Spec Reference

Specs are organized in a team-based hierarchy under `specs/`. Each team defines its APIs in `api.yaml` and can optionally override SLO thresholds in `sla.yaml`. A global `sla.yaml` provides default SLO thresholds for all APIs.

## Directory Structure

```
specs/
  sla.yaml                          # global default SLOs (required)
  teams/
    payments/
      api.yaml                      # API definitions (required per team)
      sla.yaml                      # team-specific SLO overrides (optional)
    integrations/
      api.yaml
      sla.yaml
```

Each directory under `specs/teams/` represents a team. The pipeline automatically discovers all team directories.

## Global SLA Format (`specs/sla.yaml`)

Defines default SLO thresholds that apply to all APIs unless overridden by a team SLA. Must contain a wildcard (`*`) entry.

```yaml
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

### Global SLA Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `apis` | yes | list | List of SLA entries. Must include a `name: "*"` wildcard entry. |
| `apis[].name` | yes | string | API name to match, or `"*"` for the wildcard default. |
| `apis[].slo` | yes | object | SLO definitions keyed by type (`error_rate`, `latency`). |

### SLO Entry Fields

Each SLO type (`error_rate`, `latency`) has these fields:

| Field | Required | Type | Description |
|---|---|---|---|
| `threshold` | yes | number | Threshold value. Must be a positive number. |
| `operator` | yes | string | Comparison operator (e.g., `">"`). |
| `unit` | yes | string | Unit of the threshold (`percent`, `ms`, `s`). |
| `window` | no | string | Lookback window for the query. Default: `5m`. |
| `alert` | no | boolean | Whether to generate an alert for this SLO type. Default: `true`. |

## Team API Format (`specs/teams/<team>/api.yaml`)

Defines the APIs owned by a team. Each team must have an `api.yaml`.

```yaml
apis:
  - name: v1-transactions-allowed-amounts-post
    methods:
      - POST
    paths:
      - /v1/transactions/allowed-amounts
    service:
      name: formance-service
    tags:
      team: payments
      tier: critical
      product: wallet

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

### API Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `apis` | yes | list | List of API definitions. Must be non-empty. |
| `apis[].name` | yes | string | Unique API identifier. Used in alert titles and labels. Must be unique across all teams. |
| `apis[].methods` | yes | list | HTTP methods (e.g., `GET`, `POST`). Must be non-empty. |
| `apis[].paths` | yes | list | API paths (e.g., `/v1/payments/initiate`). The first path is used as the endpoint in queries. Must be non-empty. |
| `apis[].service.name` | yes | string | Name of the service that owns this API. Used as a label. |
| `apis[].tags.team` | yes | string | Team name. Used as a label. |
| `apis[].tags.tier` | no | string | Tier level (e.g., `critical`, `high`, `medium`). Used as a label. |
| `apis[].tags.product` | no | string | Product name. Used as a label. |

## Team SLA Format (`specs/teams/<team>/sla.yaml`)

Overrides SLO thresholds for specific APIs in the team. This file is optional. If absent, all APIs in the team use the global SLA defaults.

```yaml
apis:
  - name: v1-transactions-allowed-amounts-post
    slo:
      error_rate:
        threshold: 2
        operator: ">"
        unit: percent
        window: 5m
        alert: true
      latency:
        threshold: 500
        operator: ">"
        unit: ms
        window: 5m
        alert: true

  - name: v1-payments-initiate-post
    slo:
      latency:
        threshold: 800
        operator: ">"
        unit: ms
        window: 5m
        alert: true
```

### Team SLA Fields

| Field | Required | Type | Description |
|---|---|---|---|
| `apis` | yes | list | List of API SLA overrides. |
| `apis[].name` | yes | string | Must match a `name` from the team's `api.yaml`. |
| `apis[].slo` | yes | object | SLO definitions keyed by type (`error_rate`, `latency`). |

Each SLO entry uses the same fields as the [global SLA](#slo-entry-fields).

> **Note:** API names in `sla.yaml` must correspond to APIs defined in the same team's `api.yaml`. The validator will reject unknown API names.

## SLA Resolution Rules

For each API, the pipeline resolves SLO thresholds using this precedence:

1. **Team SLA** — If the API has an entry in `specs/teams/<team>/sla.yaml`, use the SLO values defined there.
2. **Global SLA** — For any SLO type not present in the team SLA (or if the team has no `sla.yaml`), fall back to the wildcard (`*`) entry in `specs/sla.yaml`.
3. **Per SLO type** — Resolution happens independently for each SLO type. An API can get `error_rate` from the global SLA and `latency` from its team SLA.
4. **Alert flag** — Only SLO types with `alert: true` generate alert rules.

### Resolution Example

Given:
- Global SLA: `error_rate` at 5%, `latency` at 1000ms
- Team SLA for `v1-payments-initiate-post`: `latency` at 800ms (no `error_rate` override)

The resolved SLOs for `v1-payments-initiate-post` are:
- `error_rate`: 5% (from global, no team override)
- `latency`: 800ms (from team SLA)

## Duration Format

Duration fields (`window`) use the format `<number><unit>`:

| Unit | Meaning | Example |
|---|---|---|
| `s` | seconds | `30s` |
| `m` | minutes | `5m` |
| `h` | hours | `1h` |

## Validation Rules

The pipeline validates every spec file before building. These checks are enforced:

1. **Global SLA exists** — `specs/sla.yaml` must be present and contain a wildcard (`*`) entry.
2. **Team directory** — `specs/teams/` must exist and contain at least one team.
3. **api.yaml required** — Each team directory must have an `api.yaml`.
4. **API fields** — Each API must have `name`, `methods`, `paths`, `service.name`, and `tags.team`.
5. **Unique API names** — API names must be unique across all teams.
6. **SLA references** — API names in a team's `sla.yaml` must match APIs in that team's `api.yaml`.
7. **SLO values** — Thresholds must be positive numbers, operators and units must be strings, windows must be valid durations.

If any check fails, the pipeline exits with an error before generating anything.

## Alert Naming

Alert titles follow this format:

```
<api-name> <slo-type-label> above <threshold><unit>
```

Examples:
- `v1-transactions-allowed-amounts-post error rate above 2%`
- `v1-payments-initiate-post latency above 800ms`
- `v1-webhooks-receive-post error rate above 5%`

## Alert Labels

Labels are merged from multiple sources:

| Label | Source |
|---|---|
| `team` | `api.yaml` tags |
| `tier` | `api.yaml` tags |
| `product` | `api.yaml` tags |
| `service` | `api.yaml` service.name |
| `api_name` | `api.yaml` name |
| `endpoint` | `api.yaml` paths (first entry) |
| `env` | From `envArray` in global config |
| `alert_type` | SLO type (`error_rate` or `latency`) |
| (any) | `alertPlatform.labels` from global config |

## Alert Grouping

Alerts are grouped by `(environment, eval_interval)`. The group name follows the pattern:

```
api-alerts-{env}-{interval_seconds}s
```

For example, with default `window: 5m`:
- Group name: `api-alerts-prod-300s`

The evaluation interval is derived from the SLO `window` field.

## Generated Output

For each API, each SLO type (where `alert: true`), and each environment, the pipeline generates an alert rule with:

- **Title:** `<api-name> <slo-type> above <threshold><unit>`
- **Labels:** Merged from API tags, global config, and environment
- **Annotations:** Auto-generated summary and description
- **Query:** The query template with `{endpoint}`, `{env}`, `{table}` substituted
- **Condition:** 3-step evaluation (query, reduce, threshold comparison)
