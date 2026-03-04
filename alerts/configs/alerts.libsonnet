{
  // Default evaluation configuration
  defaultEvalConfig: {
    interval: 60,
    pendingPeriod: '5m',
    keepFiringFor: '',
  },

  // Default data query configuration
  defaultDataConfig: {
    database: '<your-database>',
    datasource: {
      type: '<your-datasource-type>',
      uid: '<your-datasource-uid>',
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
