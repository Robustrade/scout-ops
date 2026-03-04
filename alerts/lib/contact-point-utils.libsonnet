/*
  Creates a new alert contact point
  
  Parameters:
  - name: Name of the contact point (must be unique)
  - type: Type of the contact point (e.g., 'email', 'slack', 'webhook', 'pagerduty', etc.)
  - settings: Object containing configuration specific to the contact point type.
             The structure of this object depends on the contact point type:
             - For 'email': { addresses: 'email1@example.com;email2@example.com' }
             - For 'slack': { url: 'https://hooks.slack.com/...', title: 'Alert' }
             - For 'webhook': { url: 'https://example.com/webhook', httpMethod: 'POST' }
             - For 'pagerduty': { integrationKey: 'your-key-here' }
             Refer to the alerting platform's documentation for the full list of supported types and their settings.
  - orgId: Organization ID (default: 1)
  - disableResolveMessage: Whether to disable the resolve message (default: false)
*/
local createContactPoint(
  name,
  type='email', 
  settings, 
  orgId=1,
  disableResolveMessage=false,
) = {
    apiVersion: 'grizzly.grafana.com/v1alpha1',
    kind: 'AlertContactPoint',
    metadata: { name: name },
    spec: {
      orgId: orgId,
      disableResolveMessage: disableResolveMessage,
      name: name,
      settings: settings,
      type: type,
    },
  };

{
    createContactPoint: createContactPoint,
}

