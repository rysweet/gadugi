# Hierarchical Memory System

A simplified memory management system using pure Markdown files organized in a hierarchical structure, replacing the complex GitHub Issues sync system.

## Repository Size Considerations

When implementing the hierarchical memory system, it's important to consider the impact on git repository size and performance:

### Storage Impact

**Memory File Growth**:
- Memory files are stored as Markdown in `.memory/` directory
- Each memory level can accumulate entries over time
- Agent memories tend to grow fastest as they record frequent activities
- Project and team memories typically grow more slowly

**Repository Size Guidelines**:
- **Small Projects** (< 10 contributors): Memory files typically add 1-5MB over time
- **Medium Projects** (10-50 contributors): Expect 5-20MB growth with active agent usage
- **Large Projects** (50+ contributors): May see 20-100MB+ depending on memory retention policies

### Git Performance Considerations

**Advantages of Markdown Storage**:
- Text-based files compress well in git
- Incremental changes create small diffs
- Easy to review changes in PRs
- Version history provides audit trail

**Performance Impact**:
- Memory files are included in every clone/fetch operation
- Frequent memory updates can create many small commits
- Repository traversal includes memory files in searches

### Mitigation Strategies

**Memory Retention Policies**:
```markdown
## Recommended Retention
- **Task Memory**: 7-30 days (not checked into git)
- **Agent Memory**: 90 days for active entries
- **Project Memory**: Permanent but periodically cleaned
- **Team Memory**: Permanent (typically small and stable)
```

**Repository Management**:
1. **Regular Cleanup**: Use memory manager to prune old entries
2. **Archive Strategy**: Move old memories to archive files
3. **Git Ignore**: Task memories are automatically excluded from git
4. **Selective Storage**: Only persistent memory levels are version-controlled

**Size Monitoring**:
```bash
# Check memory directory size
du -sh .memory/

# Monitor git repository size impact
git count-objects -vH

# Check memory file growth over time
git log --stat --since="1 month ago" -- .memory/
```

### Best Practices

**For Small Teams**:
- Default retention policies work well
- Monitor memory growth quarterly
- Clean up agent memories monthly

**For Large Teams**:
- Implement stricter retention policies
- Consider memory archiving strategy
- Monitor repository size weekly
- Use automation for memory cleanup

**Memory Efficiency Tips**:
- Avoid storing large data in memory entries
- Use concise, meaningful memory content
- Regularly review and clean project memories
- Consider separating frequently-changing data to task memory

### Alternative Approaches

If repository size becomes a concern:

**External Storage**:
- Store memories in separate repository
- Reference via git submodules
- Use external database for high-frequency data

**Hybrid Approach**:
- Keep critical memories in git
- Store detailed logs externally
- Reference external storage in memory entries

### Monitoring Commands

```bash
# Check current memory system size
python3 .memory_utils/memory_manager.py stats

# Analyze memory growth patterns
python3 .memory_utils/memory_manager.py analyze --since="1 month"

# Clean up old memories
python3 .memory_utils/memory_manager.py cleanup --older-than=90days
```

This design balances simplicity with scalability, providing a foundation that grows appropriately with project complexity while maintaining git repository performance.