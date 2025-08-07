# Memory Manager Agent

The Memory Manager Agent is responsible for managing AI assistant memory, maintaining context persistence, and synchronizing project state with GitHub Issues.

## Overview

This agent specializes in:
- **Memory Management**: Maintaining and optimizing Memory.md content
- **GitHub Integration**: Synchronizing tasks with GitHub Issues
- **Context Persistence**: Ensuring continuity between AI sessions  
- **Content Organization**: Structuring information for maximum utility

## Key Features

### Memory Operations
- **Update**: Add new accomplishments, goals, and context
- **Prune**: Remove outdated information while preserving critical context
- **Archive**: Move completed items to appropriate storage
- **Optimize**: Balance detail with conciseness

### GitHub Synchronization
- **Bidirectional Sync**: Keep Memory.md and Issues in sync
- **Automatic Issue Creation**: Create issues for new tasks
- **Status Updates**: Update issue status based on task progress
- **Label Management**: Apply appropriate labels and metadata

### Content Structure
- **Standardized Format**: Consistent Memory.md organization
- **Priority-Based Ordering**: Most important items first
- **Cross-Reference Links**: Maintain connections between related items
- **Historical Context**: Preserve critical decisions and learnings

## Usage

### Basic Memory Update
```json
{
  "action": "update",
  "updates": [
    {
      "type": "accomplishment",
      "content": "Completed feature X implementation",
      "priority": "high",
      "metadata": {
        "pr_number": 123,
        "branch": "feature/x"
      }
    }
  ]
}
```

### GitHub Synchronization
```json
{
  "action": "sync",
  "sync_options": {
    "create_issues": true,
    "close_completed": true,
    "update_labels": true
  }
}
```

### Memory Pruning
```json
{
  "action": "prune",
  "prune_options": {
    "archive_completed": true,
    "days_threshold": 7,
    "preserve_critical": true
  }
}
```

## Integration

### With Other Agents
- **Orchestrator**: Provides memory context for coordination
- **Workflow Manager**: Records workflow progress and outcomes
- **Code Reviewer**: Captures review insights and improvements
- **Team Coach**: Shares performance metrics and optimizations

### With Development Workflow
- **Issue Lifecycle**: Tracks issues from creation to closure
- **PR Management**: Records PR creation, review, and merge
- **Branch Tracking**: Maintains current branch context
- **Release Planning**: Updates goals based on milestones

## Configuration

### Memory Settings
- `max_memory_size`: Maximum Memory.md file size (default: 100KB)
- `retention_days`: Days to retain completed tasks (default: 7)
- `priority_sections`: Required sections in Memory.md
- `archive_location`: Path for archived content

### GitHub Settings
- `sync_interval`: How often to sync with GitHub (default: hourly)
- `issue_labels`: Default labels for synchronized issues
- `rate_limit_buffer`: Buffer for GitHub API rate limits
- `retry_attempts`: Number of retry attempts for failed operations

## Performance Characteristics

### Memory Operations
- **Update Latency**: < 5 seconds for typical updates
- **Pruning Efficiency**: Removes 70-80% of outdated content
- **Context Preservation**: > 95% retention of critical information
- **File Size Optimization**: Maintains optimal size for quick loading

### GitHub Integration
- **Sync Success Rate**: > 95% successful synchronizations
- **Issue Creation**: < 10 seconds per issue
- **Bulk Operations**: Efficiently handles multiple updates
- **Error Recovery**: Graceful handling of API failures

## Best Practices

### Memory Management
1. **Regular Updates**: Update after each significant accomplishment
2. **Structured Content**: Use consistent formatting and organization
3. **Priority Focus**: Emphasize current goals and critical context
4. **Historical Perspective**: Preserve important decisions and learnings

### GitHub Integration
1. **Consistent Labeling**: Use standard labels across all issues
2. **Clear Descriptions**: Provide detailed context in issue descriptions
3. **Regular Synchronization**: Sync frequently during active development
4. **Error Monitoring**: Monitor and address synchronization failures

### Content Organization
1. **Logical Grouping**: Group related information together
2. **Chronological Order**: Order items by recency within sections
3. **Cross-References**: Link related items and external resources
4. **Actionable Items**: Make todo items clear and specific

## Troubleshooting

### Common Issues

#### Memory File Corruption
- **Symptoms**: Parse errors, malformed structure
- **Solution**: Restore from backup, validate structure
- **Prevention**: Regular backups, structure validation

#### GitHub Sync Failures
- **Symptoms**: Issues not created/updated, API errors
- **Solution**: Check rate limits, retry with backoff
- **Prevention**: Monitor API usage, implement proper retry logic

#### Context Loss
- **Symptoms**: Missing critical information, poor continuity
- **Solution**: Review retention policies, restore from archive
- **Prevention**: Careful pruning rules, critical context marking

### Performance Issues

#### Large Memory Files
- **Symptoms**: Slow loading, context overload
- **Solution**: Aggressive pruning, archive historical content
- **Prevention**: Regular maintenance, size monitoring

#### Slow GitHub Operations
- **Symptoms**: Long sync times, timeouts
- **Solution**: Batch operations, parallel processing
- **Prevention**: Efficient API usage, proper pagination

## Testing

The Memory Manager Agent includes comprehensive tests covering:
- **Memory Operations**: Update, prune, archive functionality
- **GitHub Integration**: Issue creation, updates, synchronization
- **Content Validation**: Structure validation, format checking
- **Error Handling**: API failures, file corruption recovery
- **Performance**: Large file handling, bulk operations

Run tests with:
```bash
python -m pytest tests/test_memory_manager.py -v
```

## Future Enhancements

### Planned Features
- **Smart Pruning**: ML-based content importance scoring
- **Advanced Search**: Semantic search across memory content
- **Trend Analysis**: Pattern recognition in project evolution
- **Integration APIs**: RESTful API for external tool integration

### Potential Improvements
- **Real-time Sync**: WebSocket-based live synchronization
- **Version Control**: Track memory changes over time
- **Collaboration**: Multi-user memory management
- **Analytics**: Detailed memory usage and effectiveness metrics