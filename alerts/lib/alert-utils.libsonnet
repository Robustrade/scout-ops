local createOrUpdateAlertRuleGroup(
  title,
  folderUid,
  interval,
  rules=[],
) = {
  apiVersion: 'grizzly.grafana.com/v1alpha1',
  kind: 'AlertRuleGroup',
  metadata: {
    name: folderUid + '.' + title,
  },
  spec: {
    interval: interval,
    rules: rules,
    folderUid: folderUid,
    title: title,
  },
};

{
  createOrUpdateAlertRuleGroup: createOrUpdateAlertRuleGroup,
}