# Simple Calculator Design

## Architecture
Single Python module with calculator functions.

## Components

### Calculator Module
- **Type**: library
- **File**: src/calculator.py
- **Description**: Provides basic arithmetic operations

## Implementation Details

### Functions
- `add(a: float, b: float) -> float`: Returns a + b
- `subtract(a: float, b: float) -> float`: Returns a - b  
- `multiply(a: float, b: float) -> float`: Returns a * b
- `divide(a: float, b: float) -> float`: Returns a / b with zero check

### Error Handling
- Raise `ValueError` for non-numeric inputs
- Raise `ZeroDivisionError` for division by zero

## Technology Stack
- **Language**: Python 3.12
- **Type Checking**: pyright
- **Formatting**: ruff