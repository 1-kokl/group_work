const path = require('path');

module.exports = {
  rootDir: path.resolve(__dirname, '../../'),
  testMatch: ['<rootDir>/tests/api/**/*.spec.js'],
  setupFilesAfterEnv: ['<rootDir>/tests/api/setup.js'],
  testEnvironment: 'node',
  transform: {
    '^.+\\.jsx?$': 'babel-jest'
  }
};

