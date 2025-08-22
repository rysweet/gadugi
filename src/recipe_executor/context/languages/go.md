# Go-Specific Guidelines

## Language Standards

### Code Quality Requirements
- **Format**: MUST be formatted with `gofmt` or `goimports`
- **Lint**: MUST pass `golangci-lint` with no errors
- **Vet**: MUST pass `go vet` with no issues
- **Documentation**: MUST include godoc comments for all exported items

### Project Structure
```
project/
├── cmd/
│   └── app/
│       └── main.go
├── internal/
│   ├── config/
│   ├── handlers/
│   └── services/
├── pkg/
│   └── utils/
├── tests/
├── go.mod
├── go.sum
├── Makefile
└── README.md
```

### Testing Framework
- Use standard `testing` package
- Include table-driven tests
- Use `testify` for assertions if needed
- Include benchmarks for performance-critical code

### Go-Specific Patterns

#### Error Handling
```go
// Custom error types
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed for %s: %s", e.Field, e.Message)
}

// Error wrapping
if err != nil {
    return fmt.Errorf("failed to process: %w", err)
}
```

#### Interfaces
```go
// Define interfaces at the point of use
type Repository interface {
    Get(ctx context.Context, id string) (*Entity, error)
    Save(ctx context.Context, entity *Entity) error
    Delete(ctx context.Context, id string) error
}

// Accept interfaces, return structs
func NewService(repo Repository) *Service {
    return &Service{repo: repo}
}
```

#### Context Usage
```go
func ProcessRequest(ctx context.Context, req *Request) (*Response, error) {
    // Check context cancellation
    select {
    case <-ctx.Done():
        return nil, ctx.Err()
    default:
    }
    
    // Process with timeout
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()
    
    return process(ctx, req)
}
```

#### Concurrency
```go
// Use channels for communication
func worker(jobs <-chan Job, results chan<- Result) {
    for job := range jobs {
        result := processJob(job)
        results <- result
    }
}

// Use sync.WaitGroup for coordination
var wg sync.WaitGroup
for i := 0; i < numWorkers; i++ {
    wg.Add(1)
    go func() {
        defer wg.Done()
        worker(jobs, results)
    }()
}
wg.Wait()
```

### Best Practices
- Keep interfaces small and focused
- Return early to reduce nesting
- Use defer for cleanup
- Handle errors explicitly
- Use context for cancellation
- Prefer composition over inheritance
- Make zero values useful