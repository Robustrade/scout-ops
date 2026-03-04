// Helper function to create a dashboard folder
local createFolder(name="env+name", title= 'env+name') = {
  apiVersion: 'grizzly.grafana.com/v1alpha1',
  kind: 'DashboardFolder',
  metadata: {
    name: name,
  },
  spec: {
    title: title,
  },
};

{
  createFolder: createFolder,
}
