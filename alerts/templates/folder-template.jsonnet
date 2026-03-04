local folderUtils = import '../lib/folder-utils.libsonnet';

// Template function to create environment folders
local createFolder(env) = 
  folderUtils.createFolder(
    name=env + '-platform',
    title=std.asciiUpper(env) + ' Platform Monitoring'
  );

{
  createFolder: createFolder
}