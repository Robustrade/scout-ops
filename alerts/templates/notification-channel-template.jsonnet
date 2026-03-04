local contactPointUtils = import '../lib/contact-point-utils.libsonnet';

// Template function to create contact points for an environment
local createContactPointWithIntegrations(env, secrets) = [
  contactPointUtils.createContactPoint(
    name='slack-' + env,
    type='slack',
    settings={
      url: secrets[env].slackUrl,
      title: 'Alert from ' + env,
      text: 'Alert: {{ range .Alerts }}{{ .Annotations.summary }}{{ end }}',
    }
  ),
  contactPointUtils.createContactPoint(
    name='pagerduty-' + env,
    type='pagerduty',
    settings={
      integrationKey: secrets[env].pagerDutyKey,
      severity: 'critical',
      component: 'alerts',
      group: env + '-alerts',
    }
  ),
];

{
  createContactPointWithIntegrations: createContactPointWithIntegrations,
}
