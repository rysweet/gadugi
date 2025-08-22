# TypeScript-Specific Guidelines

## Language Standards

### Code Quality Requirements
- **Type Safety**: MUST use strict TypeScript with no `any` types
- **TSConfig**: MUST use strict mode in tsconfig.json
- **ESLint**: MUST pass ESLint with TypeScript rules
- **Prettier**: MUST be formatted with Prettier
- **Documentation**: MUST include JSDoc/TSDoc comments

### Project Structure
```
project/
├── src/
│   ├── index.ts
│   ├── types/
│   ├── services/
│   └── utils/
├── tests/
│   ├── unit/
│   └── integration/
├── package.json
├── tsconfig.json
├── .eslintrc.json
├── .prettierrc
└── jest.config.js
```

### Testing Framework
- Use `jest` with `ts-jest` for testing
- Write tests in TypeScript
- Use type-safe mocks and stubs
- Include test coverage reporting

### TypeScript-Specific Patterns

#### Type Definitions
```typescript
// Use interfaces for object shapes
interface User {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}

// Use types for unions and aliases
type Status = 'pending' | 'active' | 'inactive';
type UserId = string;

// Use enums sparingly, prefer const assertions
const Status = {
  PENDING: 'pending',
  ACTIVE: 'active',
  INACTIVE: 'inactive'
} as const;
type StatusType = typeof Status[keyof typeof Status];
```

#### Generics
```typescript
function processArray<T>(items: T[], processor: (item: T) => T): T[] {
  return items.map(processor);
}

class Repository<T extends { id: string }> {
  private items: Map<string, T> = new Map();
  
  add(item: T): void {
    this.items.set(item.id, item);
  }
  
  get(id: string): T | undefined {
    return this.items.get(id);
  }
}
```

#### Error Handling
```typescript
class ApplicationError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = 500
  ) {
    super(message);
    this.name = 'ApplicationError';
  }
}

// Result type for functional error handling
type Result<T, E = Error> = 
  | { success: true; data: T }
  | { success: false; error: E };
```

### Strict Configuration

tsconfig.json should include:
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true
  }
}
```