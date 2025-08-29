# Performance Patterns and Optimization Opportunities

This document outlines performance issues and optimization patterns to identify during code reviews.

## Algorithm and Data Structure Issues

### Inefficient Data Structures
**Pattern**: Wrong data structure for the operation
**Common Issues**:
- Using lists for frequent membership tests (O(n) vs O(1))
- Using dictionaries when order matters (use OrderedDict)
- Not using sets for unique collections

**Examples**:
```python
# BAD: O(n) membership test
allowed_users = ["alice", "bob", "charlie"]
if username in allowed_users:  # O(n) lookup
    grant_access()

# GOOD: O(1) membership test
allowed_users = {"alice", "bob", "charlie"}
if username in allowed_users:  # O(1) lookup
    grant_access()
```

### Inefficient Algorithms
**Pattern**: Poor algorithmic complexity choices
**Detection**:
- Nested loops where one would suffice
- Sorting when not necessary
- Linear search in sorted data

**Examples**:
```python
# BAD: O(n²) when O(n log n) is possible
def find_duplicates_slow(items):
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i] == items[j]:
                duplicates.append(items[i])
    return duplicates

# GOOD: O(n) solution
def find_duplicates_fast(items):
    seen = set()
    duplicates = set()
    for item in items:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    return list(duplicates)
```

### Premature Optimization
**Pattern**: Optimizing before measuring
**Indicators**:
- Complex code for marginal gains
- Micro-optimizations in non-critical paths
- Reduced readability for unproven benefits

## String and Text Processing Issues

### Inefficient String Building
**Pattern**: Concatenating strings in loops
```python
# BAD: Creates new string objects each iteration
result = ""
for item in items:
    result += str(item)  # O(n²) complexity

# GOOD: More efficient building
result = "".join(str(item) for item in items)  # O(n)

# GOOD: For formatting
result = ", ".join(str(item) for item in items)
```

### Unnecessary String Operations
**Pattern**: Redundant string processing
**Examples**:
```python
# BAD: Multiple operations
text = user_input.strip().lower().strip()  # strip() called twice

# BAD: Unnecessary regex for simple operations
import re
if re.match(r'^hello', text):  # Just use str.startswith()
    pass

# GOOD: Simple string methods
if text.lower().startswith('hello'):
    pass
```

### Regular Expression Performance
**Pattern**: Inefficient regex usage
**Issues**:
- Compiling regex in loops
- Overly complex patterns
- Catastrophic backtracking

**Examples**:
```python
import re

# BAD: Compiling in loop
for text in texts:
    if re.match(r'\d{3}-\d{2}-\d{4}', text):  # Compiled each time
        process(text)

# GOOD: Pre-compile patterns
SSN_PATTERN = re.compile(r'\d{3}-\d{2}-\d{4}')
for text in texts:
    if SSN_PATTERN.match(text):
        process(text)
```

## Database and I/O Performance

### N+1 Query Problem
**Pattern**: Queries executed in loops
```python
# BAD: N+1 queries
users = User.objects.all()
for user in users:
    profile = user.profile  # Separate query for each user

# GOOD: Eager loading
users = User.objects.select_related('profile').all()
for user in users:
    profile = user.profile  # No additional query
```

### Inefficient Database Queries
**Pattern**: Poor query optimization
**Issues**:
- Missing database indexes
- Selecting unnecessary columns
- Not using bulk operations

**Examples**:
```python
# BAD: Individual operations
for item in items:
    Item.objects.create(name=item.name, value=item.value)

# GOOD: Bulk creation
Item.objects.bulk_create([
    Item(name=item.name, value=item.value) for item in items
])
```

### Synchronous I/O in Performance-Critical Code
**Pattern**: Blocking operations in hot paths
```python
# BAD: Synchronous I/O in loop
results = []
for url in urls:
    response = requests.get(url)  # Blocks for each request
    results.append(response.json())

# GOOD: Async or parallel processing
import asyncio
import aiohttp

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, url) for url in urls]
        return await asyncio.gather(*tasks)
```

## Memory Usage Issues

### Memory Leaks
**Pattern**: Objects not properly cleaned up
**Detection**:
- Circular references without weak references
- Event handlers not unregistered
- File handles not closed

**Examples**:
```python
# BAD: Potential memory leak
class EventManager:
    def __init__(self):
        self.handlers = []

    def add_handler(self, handler):
        self.handlers.append(handler)  # Never removed

# GOOD: Proper cleanup
class EventManager:
    def __init__(self):
        self.handlers = []

    def add_handler(self, handler):
        self.handlers.append(handler)

    def remove_handler(self, handler):
        if handler in self.handlers:
            self.handlers.remove(handler)
```

### Excessive Memory Usage
**Pattern**: Loading more data than needed
```python
# BAD: Loading entire file into memory
with open('huge_file.txt') as f:
    content = f.read()  # Could be GBs
    for line in content.split('\n'):
        process_line(line)

# GOOD: Process line by line
with open('huge_file.txt') as f:
    for line in f:  # Generator, memory efficient
        process_line(line.strip())
```

### Inefficient Data Copying
**Pattern**: Unnecessary data duplication
```python
# BAD: Creates unnecessary copies
def process_data(data):
    sorted_data = sorted(data)  # Creates new list
    filtered_data = [x for x in sorted_data if x > 0]  # Another copy
    return filtered_data

# GOOD: More efficient approach
def process_data(data):
    return sorted(x for x in data if x > 0)  # Single operation
```

## Caching Issues

### Missing Caching Opportunities
**Pattern**: Repeatedly computing expensive operations
```python
# BAD: Expensive computation repeated
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)  # Exponential time

# GOOD: Memoization
from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)  # Cached results
```

### Ineffective Caching Strategies
**Pattern**: Poor cache usage
**Issues**:
- Cache keys not normalized
- Cache without expiration
- Cache invalidation problems

**Examples**:
```python
# BAD: Poor cache key design
cache[f"{user_id}_{data}"] = result  # 'data' might be complex object

# GOOD: Proper cache key
cache_key = f"{user_id}_{hash(str(sorted(data.items())))}"
cache[cache_key] = result
```

## Concurrent Processing Issues

### Unnecessary Synchronization
**Pattern**: Over-synchronization hurting performance
```python
# BAD: Unnecessary locking for read-only operations
import threading

lock = threading.Lock()
shared_config = {}

def get_config(key):
    with lock:  # Unnecessary for reads
        return shared_config.get(key)

# GOOD: Reader-writer pattern or immutable data
import threading

config_lock = threading.RWLock()  # If available
shared_config = {}

def get_config(key):
    with config_lock.reader():
        return shared_config.get(key)
```

### Poor Parallelization
**Pattern**: Ineffective use of parallel processing
**Issues**:
- Too many threads for I/O bound tasks
- Too few processes for CPU bound tasks
- Overhead exceeding benefits

## Framework and Library Performance

### Django ORM Performance
**Common Issues**:
```python
# BAD: N+1 queries
books = Book.objects.all()
for book in books:
    print(book.author.name)  # Query per book

# GOOD: Select related
books = Book.objects.select_related('author').all()
for book in books:
    print(book.author.name)  # Single query
```

### Flask Performance Issues
```python
# BAD: Debug mode in production
app.run(debug=True)  # Never in production

# BAD: Not using application factory
app = Flask(__name__)  # Global app instance

# GOOD: Application factory pattern
def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    return app
```

## JavaScript/Frontend Performance (if reviewing JS)

### DOM Manipulation Issues
```javascript
// BAD: Multiple DOM queries
for (let i = 0; i < items.length; i++) {
    document.getElementById('container').innerHTML += `<div>${items[i]}</div>`;
}

// GOOD: Batch DOM updates
const container = document.getElementById('container');
const fragment = document.createDocumentFragment();
items.forEach(item => {
    const div = document.createElement('div');
    div.textContent = item;
    fragment.appendChild(div);
});
container.appendChild(fragment);
```

## Performance Measurement and Profiling

### Missing Performance Monitoring
**Pattern**: No performance tracking in critical code
**Recommendations**:
- Add timing for critical operations
- Monitor resource usage
- Log performance metrics

```python
import time
import logging

def performance_monitor(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        if duration > 1.0:  # Log slow operations
            logging.warning(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper
```

### Premature Optimization Detection
**Signs to flag**:
- Complex code without performance justification
- Optimization in non-critical paths
- Readability sacrificed for minimal gains

## Performance Testing Issues

### Missing Performance Tests
**Pattern**: No automated performance validation
```python
import pytest
import time

def test_search_performance():
    large_dataset = generate_test_data(10000)

    start = time.time()
    result = search_function(large_dataset, "target")
    duration = time.time() - start

    assert duration < 0.1  # Should complete in under 100ms
    assert len(result) > 0
```

### Ineffective Load Testing
**Issues**:
- Testing with unrealistic data
- Not testing concurrent scenarios
- Missing resource monitoring

## Performance Review Checklist

### High Priority (Significant Impact)
- [ ] N+1 query problems in database access
- [ ] Inefficient loops and algorithms
- [ ] Memory leaks in long-running processes
- [ ] Blocking I/O in critical paths
- [ ] Missing indexes on database queries

### Medium Priority (Moderate Impact)
- [ ] Inefficient string operations
- [ ] Missing caching opportunities
- [ ] Poor data structure choices
- [ ] Unnecessary data copying
- [ ] Suboptimal regex patterns

### Low Priority (Minor Optimizations)
- [ ] Minor algorithmic improvements
- [ ] Code style affecting performance
- [ ] Potential micro-optimizations
- [ ] Memory usage optimizations
- [ ] Configuration tuning opportunities

## Context-Aware Performance Review

### Application Type Considerations
- **Web Applications**: Focus on response time and throughput
- **Data Processing**: Emphasize algorithmic efficiency
- **Real-time Systems**: Check for timing guarantees
- **Mobile Apps**: Consider battery and memory usage

### Scale Considerations
- **Small Applications**: Focus on obvious inefficiencies
- **Large Scale**: Emphasis on scalability patterns
- **High Traffic**: Caching and optimization critical
- **Batch Processing**: Memory efficiency important

### Performance vs. Readability Trade-offs
- **Early Development**: Favor clarity over optimization
- **Performance Critical**: Justify complexity with measurements
- **Maintenance Phase**: Balance optimization with maintainability
- **Legacy Systems**: Incremental improvements preferred

## Tools and Techniques

### Profiling Tools (Python)
- **cProfile**: Built-in profiler
- **py-spy**: Sampling profiler
- **memory_profiler**: Memory usage analysis
- **line_profiler**: Line-by-line timing

### Database Performance
- **EXPLAIN plans**: Query execution analysis
- **Index analysis**: Missing index detection
- **Query logs**: Slow query identification

### General Performance Monitoring
- **APM tools**: Application performance monitoring
- **Metrics collection**: System resource tracking
- **Load testing**: Performance under stress
