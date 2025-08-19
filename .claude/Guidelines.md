# Gadugi Development Guidelines

## CRITICAL: Zero BS Principle

**NO BULLSHIT. NO CLAIMS WITHOUT EVIDENCE. NO FAKE COMPLETIONS.**

- If code doesn't exist, say "NOT IMPLEMENTED"
- If it's a stub, say "STUB ONLY"
- If it's untested, say "UNTESTED"
- If it doesn't work, say "BROKEN"
- NEVER claim something is complete unless it actually works end-to-end

## Core Development Principles

### 1. Ruthless Honesty
- Admit what's not done
- Acknowledge what's broken
- Report actual status, not aspirational status
- If you haven't tested it, don't claim it works

### 2. Implementation Before Claims
- Write the code first
- Test it second
- Document it third
- Claim completion only after all three

### 3. Recipe-Driven Development
Every component needs:
- **Requirements**: What it MUST do (not what we hope it does)
- **Design**: How it will actually work (not hand-waving)
- **Implementation**: Real code that runs (not stubs)
- **Tests**: Proof that it works (not hope)

### 4. Quality Gates (MANDATORY)
Before ANY code is considered complete:
- ✅ Passes `uv run pyright` with ZERO errors
- ✅ Formatted with `uv run ruff format`
- ✅ Passes `uv run ruff check`
- ✅ Has actual tests that pass with `uv run pytest`
- ✅ Pre-commit hooks pass
- ✅ Code review completed
- ✅ System design review completed

### 5. Dependency-Driven Order
- Build foundations first
- Don't build on top of stubs
- Test each layer before building the next
- If a dependency is broken, stop and fix it

### 6. Testing Requirements
- Every function needs a test
- Every API endpoint needs integration tests
- Every service needs end-to-end tests
- No "it should work" - prove it works

### 7. Review Requirements
EVERY implementation needs:
1. Design review (before coding)
2. Code review (after coding)
3. System design review (after integration)
4. Sign-off from review agent

## Implementation Checklist

For EVERY component:
- [ ] Recipe exists (requirements.md, design.md, dependencies.json)
- [ ] Implementation matches recipe requirements
- [ ] All dependencies are actually implemented (not stubs)
- [ ] Unit tests exist and pass
- [ ] Integration tests exist and pass
- [ ] Pyright passes with zero errors
- [ ] Ruff format and check pass
- [ ] Pre-commit hooks configured and pass
- [ ] Code review completed
- [ ] System design review completed
- [ ] Actually works when run (not just compiles)

## Humility Principle
- No performance claims without benchmarks
- No "production-ready" claims without production testing
- No "complete" claims without end-to-end validation
- Let the code speak for itself

## The Truth Test
Before claiming anything:
1. Can I run it right now?
2. Does it actually do what the requirements say?
3. Have I tested it with real data?
4. Would I bet money that it works?

If any answer is "no", then it's NOT DONE.
