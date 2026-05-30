const { defineConfig } = require('cypress');

module.exports = defineConfig({
  video: false,
  chromeWebSecurity: false,
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'http://localhost:5000'
  },
  e2e: {
    baseUrl: process.env.VITE_APP_BASE_URL || 'http://localhost:8080',
    supportFile: 'cypress/support/e2e.js',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}'
  }
});

