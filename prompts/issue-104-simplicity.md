## Task: Enhance CodeReviewer Agent with Design Simplicity and Over-Engineering Detection

**Issue #104**: "code reviewer needs to think carefully about simplicity of design/avoid over-engineering"

### Requirements to Implement:

1. **Add Design Simplicity Evaluation Criteria** to the CodeReviewer agent:
   - Abstraction Appropriateness evaluation
   - YAGNI (You Aren't Gonna Need It) compliance checking
   - Cognitive Load assessment
   - Solution-Problem Fit analysis

2. **Add Over-Engineering Detection Patterns**:
   - Detect generic interfaces with only one implementation
   - Identify configuration options without clear use cases
   - Find design patterns applied to simple logic
   - Spot excessive layering and indirection
   - Detect complex inheritance for simple variations
   - Identify premature optimization

3. **Add Simplicity Recommendations Section**:
   - Suggest simpler alternatives when complexity isn't justified
   - Recommend when to inline vs. abstract
   - Identify opportunities to reduce cognitive load
   - Guide toward incremental complexity introduction

4. **Add Context-Aware Assessment**:
   - Consider early-stage vs. mature project context
   - Evaluate high-change areas vs. stable domains

### Files to Modify:
- **Primary**: `.claude/agents/CodeReviewer.md` - Add new sections for design simplicity assessment
- **Test**: Create test cases to validate the new functionality

### Success Criteria:
- CodeReviewer evaluates design simplicity in all reviews
- Identifies common over-engineering patterns
- Provides actionable simplification recommendations
- Considers project context appropriately
- No false positives for justified complexity

Create branch `enhancement/issue-104-simplicity-detection` and submit PR to resolve Issue #104.
EOF < /dev/null
