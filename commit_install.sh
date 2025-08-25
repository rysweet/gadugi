#!/bin/bash
cd /Users/ryan/gadugi7/gadugi
git add install.sh README.md
git commit -m "feat: implement simple non-disruptive Gadugi installation

Following Guidelines philosophy:
- Ruthless Simplicity: One script, direct implementation
- Zero BS: Everything works or fails clearly
- No Future-Proofing: Solves today's problem only
- Present-Moment Focus: Install what's needed now

Changes:
- Add install.sh - Simple bootstrap installation script
- Update README.md - Replace complex setup with simple curl command
- Test installation creates .claude/ structure correctly
- Bootstrap approach enables deployment to any repository

Closes #231

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push -u origin feature/simple-nondisruptive-install
