local alertUtils = import '../lib/alert-utils.libsonnet';
local defaultConfig = import '../configs/alerts.libsonnet';

// Import default configurations
local defaultEvalConfig = defaultConfig.defaultEvalConfig;
local defaultDataConfig = defaultConfig.defaultDataConfig;
local defaultEvaluator = defaultConfig.defaultEvaluator;
local defaultReducer = defaultConfig.defaultReducer;
local defaultRelativeTimeRange = defaultConfig.defaultRelativeTimeRange;

// Template function that creates alert rule groups from config
local createAlertRuleGroup(title, folderUid, alertRules, interval=300, teamConfig = null) =
  local rules = [
    {
      ruleGroup: title,
      title: rule.title,
      condition: 'C',
      data: [
        {
          refId: 'A',
          queryType: '',
          relativeTimeRange: defaultRelativeTimeRange,
          datasourceUid: defaultDataConfig.datasource.uid,
          model: {
            adHocFilters: [],
            adHocValuesQuery: "",
            add_metadata: true,
            contextWindowSize: "10",
            extrapolate: true,
            database: defaultDataConfig.database  ,
            datasource: defaultDataConfig.datasource,
            query: rule.query,
            relativeTimeRange: if std.objectHas(rule, 'relativeTimeRange') && rule.relativeTimeRange != null then rule.relativeTimeRange else defaultRelativeTimeRange,
            dateTimeColDataType: if std.objectHas(rule, 'dateTimeColDataType') && rule.dateTimeColDataType != null then rule.dateTimeColDataType else 'TimeUnix',
            dateTimeType: if std.objectHas(rule, 'dateTimeType') && rule.dateTimeType != null then rule.dateTimeType else 'DATETIME64',
            format: if std.objectHas(rule, 'format') && rule.format != null then rule.format else 'time_series',
            table: if std.objectHas(rule, 'table') && rule.table != null then rule.table else '',
            refId: 'A'
          }
        },
        {
          refId: 'B',
          datasourceUid: '__expr__',
          model: {
            conditions: [
              {
                evaluator: defaultEvaluator,
                operator: { type: 'and' },
                query: { params: ['B'] },
                reducer: defaultReducer,
                type: 'query'
              }
            ],
            datasource: { type: '__expr__', uid: '__expr__' },
            expression: 'A',
            intervalMs: 1000,
            maxDataPoints: 43200,
            type: 'reduce',
            refId: 'B',
            reducer : if std.objectHas(rule, 'reducerType') && rule.reducerType != null then rule.reducerType else defaultReducer.type
          }
        },
      {
          refId: 'C',
          datasourceUid: '__expr__',
          model: {
            conditions: [
              {
                evaluator: rule.evaluator,
                operator: { type: 'and' },
                query: { params: ['C'] },
                reducer: defaultReducer,
                type: 'query'
              }
            ],
            datasource: { type: '__expr__', uid: '__expr__' },
            expression: 'B',
            intervalMs: 1000,
            maxDataPoints: 43200,
            type: 'threshold',
            refId: 'C'
       
          }
        }

      ],
      noDataState:  if std.objectHas(rule, 'noDataState') && rule.noDataState != null then rule.noDataState else 'NoData',
      execErrState: if std.objectHas(rule, 'execErrState') && rule.execErrState != null then rule.execErrState else 'Alerting',
      'for': if std.objectHas(rule, 'pendingPeriod') && rule.pendingPeriod != null then rule.pendingPeriod else defaultEvalConfig.pendingPeriod,
      keepFiringFor: if std.objectHas(rule, 'keepFiringFor') && rule.keepFiringFor != null then rule.keepFiringFor else defaultEvalConfig.keepFiringFor,
      annotations: rule.annotations,
      labels: (if std.objectHas(teamConfig, 'labels') && teamConfig.labels != null then teamConfig.labels else {}) + (if std.objectHas(rule, 'labels') && rule.labels != null then rule.labels else {}),
      folderUID: if std.objectHas(rule, 'folderUid') && rule.folderUid != null then rule.folderUid else teamConfig.folderUid,
      notification_settings: {
        receiver: if std.objectHas(rule, 'contactPoint') && rule.contactPoint != null 
             then rule.contactPoint 
             else teamConfig.contactPoint
      },
    } for rule in alertRules
  ];

  alertUtils.createOrUpdateAlertRuleGroup(
    title=title,
    folderUid=folderUid,
    interval=interval,
    rules=rules,
  );

// Export the createAlertGroup function
{
  createAlertRuleGroup: createAlertRuleGroup
}
