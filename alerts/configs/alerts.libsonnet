{
  // Default evaluation configuration
  defaultEvalConfig: {
    interval: 60,
    pendingPeriod: '5m',
    keepFiringFor: '',
  },

  // Default data query configuration
  defaultDataConfig: {
    database: 'kulu',
    datasource: {
      type: 'vertamedia-clickhouse-datasource',
      uid: 'ds-scout-altinity-ch',
    },
  },

  // Default evaluator configuration
  defaultEvaluator: {
    type: 'gt',
    params: [],
  },

  // Default reducer configuration
  defaultReducer: {
    type: 'last',
    params: [],
  },

  // Default relative time range
  defaultRelativeTimeRange: {
    from: 300,
    to: 0,
  },
}
