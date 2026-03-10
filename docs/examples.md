# Examples

## Adding a new team

Create a new directory under `specs/teams/` with an `api.yaml`:

```yaml
# specs/teams/checkout/api.yaml
apis:
  - name: v1-checkout-session-post
    methods:
      - POST
    paths:
      - /v1/checkout/session
    service:
      name: checkout-service
    tags:
      team: checkout
      tier: critical
      product: checkout
```

Then generate and preview:

```bash
cd alerts
make diff    # preview
make apply   # deploy
```

All APIs in the new team will use the global SLO defaults from `specs/sla.yaml` until you add a team-specific `sla.yaml`.

## Adding APIs to a team

Add entries to the `apis` list in the team's `api.yaml`:

```yaml
# specs/teams/payments/api.yaml
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

  - name: v1-refunds-create-post
    methods:
      - POST
    paths:
      - /v1/refunds/create
    service:
      name: payment-service
    tags:
      team: payments
      tier: high
      product: payments
```

Each new API gets alerts based on its resolved SLOs. API names must be unique across all teams.

## Overriding SLOs for specific APIs

Create or update the team's `sla.yaml` with overrides for specific APIs:

```yaml
# specs/teams/payments/sla.yaml
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

This produces:
- `v1-transactions-allowed-amounts-post error rate above 2%` (team override)
- `v1-transactions-allowed-amounts-post latency above 500ms` (team override)
- `v1-payments-initiate-post latency above 800ms` (team override)
- `v1-payments-initiate-post error rate above 5%` (global default, no team override for error_rate)
- `v1-refunds-create-post error rate above 5%` (global default, not in team sla.yaml)
- `v1-refunds-create-post latency above 1000ms` (global default, not in team sla.yaml)

## Using global defaults (no team sla.yaml)

If a team has no `sla.yaml`, all its APIs use the global SLO defaults:

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

```yaml
# specs/teams/integrations/api.yaml (no sla.yaml in this directory)
apis:
  - name: v1-webhooks-receive-post
    methods:
      - POST
    paths:
      - /v1/webhooks/receive
    service:
      name: webhook-service
    tags:
      team: integrations
      tier: medium
      product: webhooks
```

This generates:
- `v1-webhooks-receive-post error rate above 5%` (global default)
- `v1-webhooks-receive-post latency above 1000ms` (global default)

## Mixed overrides (some SLO types from team, others from global)

SLA resolution happens per SLO type. You can override just one type and let the other fall back to global:

```yaml
# specs/teams/integrations/sla.yaml
apis:
  - name: v1-services-process-post
    slo:
      latency:
        threshold: 2000
        operator: ">"
        unit: ms
        window: 5m
        alert: true
```

Since only `latency` is overridden for `v1-services-process-post`:
- `latency`: 2000ms (from team SLA)
- `error_rate`: 5% (from global SLA, no team override)

The other API in the team (`v1-webhooks-receive-post`) has no entry in `sla.yaml`, so it uses both global defaults.

## Disabling alerts for a specific SLO type

Set `alert: false` in the team SLA to suppress alert generation for a specific SLO type:

```yaml
# specs/teams/internal/sla.yaml
apis:
  - name: v1-health-check-get
    slo:
      error_rate:
        threshold: 5
        operator: ">"
        unit: percent
        window: 5m
        alert: false     # no error rate alert for this API
      latency:
        threshold: 200
        operator: ">"
        unit: ms
        window: 5m
        alert: true
```

This generates only the latency alert, skipping error rate.

## Multiple environments

Edit `alerts/configs/global.yaml` to add environments:

```yaml
envArray:
  - prod
  - staging
```

Every API now generates alert rules for both `prod` and `staging`. The `{env}` placeholder in the query template is substituted accordingly. Alert annotations include the environment name.

## Removing a team

Delete the team directory from `specs/teams/` and run `make apply`. Since the pipeline is fully declarative, removed teams stop generating alert rules.

> Note: The pipeline only manages what it generates. To clean up previously deployed rules that are no longer in the spec files, you may need to manually remove them from the alerting platform directly.

## Removing an API from a team

Remove the API entry from the team's `api.yaml` (and from `sla.yaml` if it has an override), then run `make apply`.
