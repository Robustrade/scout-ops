local alertTemplate = import 'templates/alert-rule-template.jsonnet';

// Generated input payloads
local teamConfig = std.parseJson(std.extVar('TEAM_CONFIGS'));
local importedResource = std.parseJson(std.extVar('ALERT_CONFIGS'));

local folderUid = teamConfig.folderUid;

[
alertTemplate.createAlertRuleGroup(
  title=alertGroup.name,
  folderUid=folderUid,
  alertRules= alertGroup.alertRules,
  interval=alertGroup.interval,
  teamConfig=teamConfig
)

for alertGroup in importedResource.alertGroups 
]
