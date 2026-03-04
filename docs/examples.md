# Examples

## Add a new endpoint

Create a new YAML file in `specs/alerts/endpoints/`:

```yaml
# specs/alerts/endpoints/health.yaml
endpoint: /api/v1/health
alerts:
  - type: latency
    threshold_ms: 50
```

Then:

```bash
cd alerts
make diff    # preview
make apply   # deploy
```

## Multiple alerts for one endpoint

Define multiple entries in the `alerts` array to create separate alert rules for the same endpoint:

```yaml
# specs/alerts/endpoints/checkout.yaml
endpoint: /api/v1/checkout
alerts:
  - type: latency
    threshold_ms: 300
    severity: warning

  - type: latency
    threshold_ms: 1000
    severity: critical
    pendingPeriod: 1m
```

This creates two alert rules:
- **Warning** at 300ms with default 2m pending period
- **Critical** at 1000ms with 1m pending period

## Different evaluation intervals

Alerts with different `eval_interval` values are placed in separate alert rule groups:

```yaml
# specs/alerts/endpoints/search.yaml
endpoint: /api/v1/search
alerts:
  - type: latency
    threshold_ms: 500
    eval_interval: 30s     # → group: endpoint-latency-prod-30s

  - type: latency
    threshold_ms: 200
    eval_interval: 1m      # → group: endpoint-latency-prod-60s (default)
```

## Override notification channel

Route specific alerts to a different notification channel:

```yaml
# specs/alerts/endpoints/billing.yaml
endpoint: /api/v1/billing
alerts:
  - type: latency
    threshold_ms: 100
    severity: critical
    contactPoint: pagerduty-billing
```

## Override folder

Store alerts in a different folder:

```yaml
# specs/alerts/endpoints/internal.yaml
endpoint: /internal/metrics
alerts:
  - type: latency
    threshold_ms: 500
    folderUid: internal-alerts-folder-uid
```

## Add extra labels

Add custom labels that get merged with the global labels:

```yaml
# specs/alerts/endpoints/payments.yaml
endpoint: /api/v1/payments
alerts:
  - type: latency
    threshold_ms: 120
    severity: critical
    labels:
      service: payment-gateway
      oncall: payments-team
```

The final labels will include the global labels (e.g., `team: devops`) plus `env`, `endpoint`, `severity`, `alert_type`, `service`, and `oncall`.

## Custom query template

Override the query template for a specific endpoint:

```yaml
# specs/alerts/endpoints/websocket.yaml
endpoint: /ws/v1/stream
alerts:
  - type: latency
    threshold_ms: 50
    query_template: |
      SELECT avg(duration_ms) FROM {table}
      WHERE time > $timeFilter
      AND path = '{endpoint}'
      AND environment = '{env}'
```

## Override lookback window

Use a longer or shorter query range:

```yaml
# specs/alerts/endpoints/batch-api.yaml
endpoint: /api/v1/batch/process
alerts:
  - type: latency
    threshold_ms: 5000
    lookback: 15m          # look back 15 minutes instead of default 5m
    eval_interval: 5m      # evaluate every 5 minutes
    severity: warning
```

## Multiple environments

Edit `alerts/configs/global.yaml` to add environments:

```yaml
envArray:
  - prod
  - staging
```

Every endpoint spec now generates alert rules for both `prod` and `staging`. The `{env}` placeholder in the query template is substituted accordingly.

## Remove an endpoint

Delete the YAML file from `specs/alerts/endpoints/` and run `make apply`. Since the pipeline is fully declarative, removed endpoints stop generating alert rules.

> Note: The pipeline only manages what it generates. To clean up previously deployed rules that are no longer in the spec files, you may need to manually remove them from the alerting platform or use `grr` CLI directly.

## Extending to new alert types

Currently only `latency` is supported. To add a new type like `error_rate`:

1. **Update validation** — Add `error_rate` to the allowed types in `alerts/scripts/validate-alerts.py`
2. **Add build logic** — Handle the new type in `alerts/scripts/build-alert-configs.py` (query template, threshold semantics, title format)
3. **Update global defaults** — Add a `defaults.error_rate` section in `alerts/configs/global.yaml`
4. **Optionally update the Jsonnet template** if the new type needs a different alert condition structure

Example spec for a future `error_rate` type:

```yaml
endpoint: /api/v1/payments
alerts:
  - type: latency
    threshold_ms: 120

  - type: error_rate
    threshold_percent: 5
    severity: critical
```
