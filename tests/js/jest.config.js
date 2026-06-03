module.exports = {
  testEnvironment: 'jsdom',
  roots: ['<rootDir>'],
  testMatch: ['**/*.test.js'],
  setupFilesAfterEnv: ['<rootDir>/setup.js'],
  moduleFileExtensions: ['js'],
  verbose: true,
  collectCoverageFrom: [
    '../../static/js/**/*.js',
    '!../../static/js/**/*.min.js'
  ],
  coverageDirectory: './coverage'
};
