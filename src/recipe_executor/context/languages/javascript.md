# JavaScript-Specific Guidelines

## Language Standards

### Code Quality Requirements
- **ESLint**: MUST pass ESLint with no errors
- **Prettier**: MUST be formatted with Prettier
- **JSDoc**: MUST include JSDoc comments for all public functions
- **Module System**: Use ES6 modules (import/export)

### Project Structure
```
project/
├── src/
│   ├── index.js
│   ├── core/
│   └── models/
├── tests/
│   ├── core.test.js
│   └── models.test.js
├── package.json
├── .eslintrc.json
├── .prettierrc
└── jest.config.js
```

### Testing Framework
- Use `jest` or `mocha` for testing
- Include test coverage reporting
- Use `describe` and `it` blocks for organization
- Mock external dependencies

### Package Management
- Use `npm` or `yarn` for dependencies
- Lock file required (`package-lock.json` or `yarn.lock`)
- Separate dev dependencies from production

### JavaScript-Specific Patterns

#### Error Handling
```javascript
class CustomError extends Error {
  constructor(message, code, details) {
    super(message);
    this.name = 'CustomError';
    this.code = code;
    this.details = details;
  }
}
```

#### Async/Await
```javascript
async function processData(data) {
  try {
    const validated = await validateData(data);
    const result = await transformData(validated);
    return result;
  } catch (error) {
    logger.error('Processing failed', error);
    throw new ProcessingError('Failed to process data', error);
  }
}
```

#### Module Exports
```javascript
// Named exports
export { functionA, functionB };

// Default export
export default MainClass;

// Re-exports
export { moduleA } from './moduleA';
```

### Promise Handling
- Always handle promise rejections
- Use async/await over .then() chains
- Implement proper error boundaries

### Logging
```javascript
const logger = {
  debug: (msg, ...args) => console.debug(`[DEBUG] ${msg}`, ...args),
  info: (msg, ...args) => console.info(`[INFO] ${msg}`, ...args),
  warn: (msg, ...args) => console.warn(`[WARN] ${msg}`, ...args),
  error: (msg, ...args) => console.error(`[ERROR] ${msg}`, ...args),
};
```