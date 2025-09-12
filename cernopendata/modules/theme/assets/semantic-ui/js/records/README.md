# CERN Open Data Portal - Records UI Testing

This directory contains the React components and utilities for the CERN Open Data Portal records interface, along with a comprehensive unit testing suite.

## 🧪 Testing Framework

The testing suite uses:
- **Jest** - JavaScript testing framework
- **React Testing Library** - React component testing utilities
- **@testing-library/user-event** - User interaction simulation
- **@testing-library/jest-dom** - Custom Jest matchers for DOM elements

## 📁 File Structure

```
records/
├── __tests__/                 # Test files
│   ├── app.test.js            # App initialization tests
│   ├── CitationsApp.test.js   # Citations component tests
│   ├── FilesBoxApp.test.js    # Files box component tests
│   ├── RequestRecord.test.js  # Request record component tests
│   ├── hooks.test.js          # Custom hooks tests
│   ├── utils.test.js          # Utility functions tests
│   ├── config.test.js         # Configuration tests
│   └── constants.test.js      # Constants tests
├── components/                # React components
├── *.js                      # Main application files
├── constants.js              # Application constants
├── hooks.js                  # Custom React hooks
├── utils.js                  # Utility functions
├── config.js                 # Configuration and URL builders
├── setupTests.js             # Test environment setup
├── jest.config.js            # Jest configuration
├── .babelrc.js              # Babel configuration
├── package.json             # Dependencies and scripts
└── README.md                # This file
```

## 🚀 Getting Started

### Prerequisites

Make sure you have Node.js >= 14.0.0 and npm >= 6.0.0 installed.

### Installation

```bash
# Install dependencies
npm install
```

### Running Tests

```bash
# Run all tests once
npm test

# Run tests in watch mode (recommended for development)
npm run test:watch

# Run tests with coverage report
npm run test:coverage

# Run tests with coverage in watch mode
npm run test:coverage:watch

# Run tests for CI (no watch, with coverage)
npm run test:ci

# Run tests in debug mode (no cache, sequential execution)
npm run test:debug

# Run tests with verbose output
npm run test:verbose
```

## 📊 Test Coverage

The test suite aims for high coverage with the following thresholds:
- **Branches**: 80%
- **Functions**: 80%
- **Lines**: 80%
- **Statements**: 80%

Coverage reports are generated in multiple formats:
- **Console output**: Summary displayed in terminal
- **HTML report**: `coverage/lcov-report/index.html`
- **LCOV format**: `coverage/lcov.info`
- **JSON summary**: `coverage/coverage-summary.json`

## 🧩 Test Categories

### 1. Component Tests
- **CitationsApp.test.js**: Tests citation display and INSPIRE API integration
- **FilesBoxApp.test.js**: Tests file listing, pagination, and data loading states
- **RequestRecord.test.js**: Tests file request functionality and modal interactions
- **app.test.js**: Tests application initialization and error handling

### 2. Hook Tests
- **hooks.test.js**: Tests custom React hooks for data fetching, citations, modals, form validation, and file availability

### 3. Utility Tests
- **utils.test.js**: Tests utility functions for file size formatting, availability checking, URL building, validation, and array operations

### 4. Configuration Tests
- **config.test.js**: Tests URL builders and configuration management
- **constants.test.js**: Tests application constants and their consistency

## 🔧 Test Configuration

### Jest Configuration (`jest.config.js`)
- **Environment**: jsdom (for DOM testing)
- **Setup**: Custom setup file with mocks and global configurations
- **Transform**: Babel for ES6+ and JSX
- **Module mapping**: CSS/SCSS files and assets
- **Coverage**: Comprehensive coverage collection and reporting

### Babel Configuration (`.babelrc.js`)
- **Presets**: @babel/preset-env and @babel/preset-react
- **Environment-specific**: Optimized for testing environment

### Setup File (`setupTests.js`)
- **Global mocks**: fetch, console methods, DOM elements
- **Test utilities**: jest-dom matchers
- **Mock configurations**: jQuery, Semantic UI, window objects

## 🎯 Testing Best Practices

### 1. Component Testing
```javascript
// Test component rendering
expect(screen.getByText('Expected Text')).toBeInTheDocument();

// Test user interactions
const user = userEvent.setup();
await user.click(screen.getByRole('button'));

// Test async operations
await waitFor(() => {
  expect(mockFunction).toHaveBeenCalled();
});
```

### 2. Hook Testing
```javascript
// Test custom hooks
const { result } = renderHook(() => useCustomHook());
expect(result.current.value).toBe(expectedValue);

// Test hook state updates
act(() => {
  result.current.updateFunction();
});
expect(result.current.value).toBe(newValue);
```

### 3. Utility Testing
```javascript
// Test pure functions
expect(utilityFunction(input)).toBe(expectedOutput);

// Test edge cases
expect(utilityFunction(null)).toBe(defaultValue);
expect(utilityFunction(edgeCase)).toBe(edgeCaseResult);
```

## 🐛 Debugging Tests

### Common Issues and Solutions

1. **Test timeouts**: Increase timeout in jest.config.js or use `jest.setTimeout()`
2. **Async operations**: Use `waitFor()` for async state updates
3. **DOM queries**: Use `screen.debug()` to see current DOM state
4. **Mock issues**: Clear mocks with `mockFn.mockClear()` in beforeEach

### Debug Commands
```bash
# Run specific test file
npm test -- CitationsApp.test.js

# Run tests matching pattern
npm test -- --testNamePattern="should render"

# Run tests with debug output
npm run test:debug -- --verbose

# Run single test in watch mode
npm run test:watch -- --testNamePattern="specific test name"
```

## 📈 Writing New Tests

When adding new components or utilities:

1. **Create test file**: Follow naming convention `*.test.js`
2. **Import dependencies**: Include necessary testing utilities
3. **Mock external dependencies**: Use jest.mock() for external modules
4. **Test all scenarios**: Happy path, error cases, edge cases
5. **Use descriptive names**: Clear test descriptions and variable names
6. **Group related tests**: Use describe blocks for organization
7. **Clean up**: Reset mocks and state in beforeEach/afterEach

### Example Test Structure
```javascript
describe('ComponentName', () => {
  beforeEach(() => {
    // Setup mocks and reset state
  });

  describe('rendering', () => {
    it('should render with default props', () => {
      // Test default rendering
    });

    it('should handle loading state', () => {
      // Test loading state
    });
  });

  describe('user interactions', () => {
    it('should handle button clicks', async () => {
      // Test user interactions
    });
  });

  describe('error handling', () => {
    it('should display error messages', () => {
      // Test error scenarios
    });
  });
});
```

## 🚨 Continuous Integration

The test suite is configured for CI environments:
- **Non-interactive mode**: Tests run without watch mode
- **Coverage reports**: Generated in CI-friendly formats
- **Error handling**: Proper exit codes for CI systems
- **Performance**: Optimized for CI execution time

Use `npm run test:ci` in CI pipelines for optimal performance and reporting.

## 📚 Additional Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro)
- [Testing Library User Events](https://testing-library.com/docs/user-event/intro)
- [Jest DOM Matchers](https://github.com/testing-library/jest-dom)

## 🤝 Contributing

When contributing to the test suite:
1. Maintain or improve test coverage
2. Follow existing testing patterns
3. Add tests for new functionality
4. Update documentation for new testing utilities
5. Run full test suite before submitting changes
