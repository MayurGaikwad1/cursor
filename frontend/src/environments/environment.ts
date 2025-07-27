export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api',
  authConfig: {
    tokenKey: 'elams_token',
    refreshTokenKey: 'elams_refresh_token',
    tokenExpiry: 30 * 60 * 1000, // 30 minutes
    refreshThreshold: 5 * 60 * 1000, // 5 minutes before expiry
  },
  features: {
    enableMFA: true,
    enableAuditLogs: true,
    enableNotifications: true,
    enableFileUpload: true,
    maxFileSize: 10 * 1024 * 1024, // 10MB
  },
  ui: {
    theme: 'default',
    itemsPerPage: 25,
    debounceTime: 300,
    toastDuration: 5000,
  },
  security: {
    enableCSP: true,
    sessionTimeout: 8 * 60 * 60 * 1000, // 8 hours
    idleTimeout: 30 * 60 * 1000, // 30 minutes
  },
  monitoring: {
    enableAnalytics: false,
    enableErrorReporting: true,
    enablePerformanceMonitoring: true,
  }
};