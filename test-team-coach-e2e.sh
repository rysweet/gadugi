#!/bin/bash

echo "🧪 Testing Team Coach End-to-End"
echo "================================"

# Test 1: Check if agent file exists
echo ""
echo "Test 1: Checking agent file exists..."
if [[ -f ".claude/agents/team-coach.md" ]]; then
    echo "✅ team-coach.md exists"
else
    echo "❌ team-coach.md NOT FOUND"
    exit 1
fi

# Test 2: Check agent uses correct invocation
echo ""
echo "Test 2: Checking agent invocation pattern..."
if grep -q "/agent:team-coach" .claude/agents/team-coach.md; then
    echo "✅ Agent uses /agent:team-coach"
else
    echo "❌ Agent does not use correct invocation"
    exit 1
fi

# Test 3: Test direct invocation (without error suppression)
echo ""
echo "Test 3: Testing direct Team Coach invocation..."
echo "Running: /agent:team-coach --test"

# Create a test session data file
cat > test-session-data.md << 'EOF'
# Test Session Data

Session ID: test-e2e-$(date +%s)
Task: End-to-end validation of Team Coach
Duration: 5 minutes
Test Results: All passing
Code Quality: Good

Please analyze this test session and provide brief coaching insights.
EOF

echo ""
echo "📝 Test session data created"
echo ""
echo "Attempting to invoke Team Coach..."
echo "NOTE: This would normally be done by Claude, testing the setup..."

# Test 4: Check workflow manager integration
echo ""
echo "Test 4: Checking workflow-manager.md integration..."
if grep -q "timeout 120 /agent:team-coach" .claude/agents/workflow-manager.md; then
    echo "✅ Workflow manager calls /agent:team-coach in Phase 13"
else
    echo "❌ Workflow manager does not properly call Team Coach"
    exit 1
fi

# Test 5: Verify no error suppression in critical path
echo ""
echo "Test 5: Checking for problematic error suppression..."
if grep "timeout 120 /agent:team-coach.*2>/dev/null" .claude/agents/workflow-manager.md; then
    echo "⚠️  WARNING: Error suppression still present (2>/dev/null)"
    echo "   This will hide 'agent not found' errors!"
else
    echo "✅ No problematic error suppression found"
fi

# Summary
echo ""
echo "================================"
echo "📊 Test Summary:"
echo "- Agent file exists: ✅"
echo "- Correct invocation pattern: ✅"
echo "- Workflow integration: ✅"
echo ""
echo "⚠️  IMPORTANT: The actual Team Coach invocation can only be"
echo "fully tested within Claude. The setup appears correct, but"
echo "we should test with a real workflow to confirm e2e functionality."
echo ""
echo "Next step: Run a workflow that triggers Phase 13 to validate"
echo "Team Coach actually executes and saves insights to Memory.md"