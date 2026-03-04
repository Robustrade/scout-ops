// Default notification policy configuration
local defaultPolicyConfig = {
  objectMatchers: [["env", "=", "stage"], ["team", "=", "sre"]],
  groupBy: ["grafana_folder", "alertname"],
  groupWait: '30s',
  groupInterval: '5m',
  repeatInterval: '4h',
};

local createNotificationPolicy(
  name,
  receiver, 
  objectMatchers=[], 
  groupBy=[],
  groupWait=defaultPolicyConfig.groupWait, 
  groupInterval=defaultPolicyConfig.groupInterval, 
  repeatInterval=defaultPolicyConfig.repeatInterval
) = {
  
           apiVersion: 'grizzly.grafana.com/v1alpha1',
           kind: 'AlertNotificationPolicy',
           metadata: {
               name: name,
           },
           spec: {
               receiver: receiver,
               object_matchers:defaultPolicyConfig.objectMatchers +   
               objectMatchers,
               group_by:  defaultPolicyConfig.groupBy + groupBy,
               group_wait: groupWait,
               group_interval: groupInterval,
               repeat_interval: repeatInterval,
           },
       };

{
  createNotificationPolicy:     createNotificationPolicy,
}