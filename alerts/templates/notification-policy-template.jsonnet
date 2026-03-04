local policyUtils = import '../lib/notification-policy-utils.libsonnet';

// Template function to create notification policies for an environment
local createGlobalPolicy(env) = 
  policyUtils.createNotificationPolicy(
    name='global-policy-' + env,
    receiver='slack-' + env,
    objectMatchers=[
      ['environment', '=', env],
    ],
    groupBy=['grafana_folder', 'alertname'],
    groupWait='10s',
    groupInterval='5m',
    repeatInterval='1h'
  ) + {
    spec+: {
      routes: [
        {
          receiver: 'pagerduty-' + env,
          object_matchers: [
            ['severity', '=', 'critical'],
            ['environment', '=', env],
          ],
          group_wait: '5s',
          group_interval: '2m',
          repeat_interval: '30m',
        },
      ],
    }
  };

{
  createGlobalPolicy: createGlobalPolicy,
}