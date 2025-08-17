# Fix Memory.md Instruction Consistency

## Task
Fix inconsistent instructions about Memory.md updates across documentation files to ensure all updates go through the memory-manager agent.

## Problem
Current instructions are contradictory:
- Some places say "UPDATE .github/Memory.md" directly
- Other places say "Use /agent:memory-manager for manual sync and maintenance"
- This causes confusion about the proper way to update Memory.md

## Requirements
1. Update CLAUDE.md to consistently state that Memory.md should be updated via memory-manager agent
2. Update claude-generic-instructions.md to consistently use memory-manager agent
3. Ensure all references to Memory.md updates point to using the agent, not direct editing
4. Keep the automatic sync functionality descriptions intact
5. Make it clear that the memory-manager agent is the ONLY approved way to update Memory.md

## Specific Changes Needed

### In CLAUDE.md:
- Line stating "Check and update @.github/Memory.md" should say "Check and update @.github/Memory.md using /agent:memory-manager"
- Add clear note that direct editing of Memory.md is discouraged

### In claude-generic-instructions.md:
- Line 7: Change "UPDATE .github/Memory.md after completing any significant task" to "UPDATE .github/Memory.md using /agent:memory-manager after completing any significant task"
- Line 103: Change "You should regularly update the memory file" to "You should regularly update the memory file using the memory-manager agent"
- Add explicit instruction: "NEVER edit Memory.md directly - always use /agent:memory-manager"

## Success Criteria
- All documentation consistently instructs to use memory-manager agent
- No contradictory instructions remain
- Clear prohibition against direct Memory.md editing
- Memory-manager agent is established as the single source of truth for Memory.md updates