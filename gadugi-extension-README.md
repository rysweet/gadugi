# Gadugi VS Code Extension

A powerful VS Code extension for managing git worktrees and Claude Code instances in parallel development workflows. This extension implements Issues #52 and #53 of the Gadugi multi-agent development system.

## Features

### 🌸 Bloom Command (Issue #52)
Automatically detects all git worktrees in your workspace, creates a new VS Code terminal for each worktree, and starts Claude Code with `--resume` in each terminal.

**Command**: `Bloom: start a new terminal for each worktree and then resume claude in that worktree`

#### What it does:
- 🔍 Discovers all git worktrees in the current workspace
- 🖥️ Creates named terminals for each worktree (`Claude: [worktree-name]`)
- 🚀 Automatically navigates to the worktree directory
- ⚡ Executes `claude --resume` in each terminal
- 📊 Provides progress feedback and error handling

### 📊 Monitor Panel (Issue #53)
Real-time monitoring panel in the VS Code sidebar showing worktrees and Claude processes with live runtime tracking.

#### What it shows:
- 📁 **Worktrees Section**: Lists all git worktrees with status indicators
- ⚡ **Processes Section**: Shows running Claude Code processes with details
- ⏱️ **Live Updates**: Runtime duration updates every 3 seconds
- 💾 **Resource Usage**: Memory usage information for processes
- 🔄 **Real-time Sync**: Automatic refresh and status updates

## Installation

### Prerequisites
- VS Code 1.74.0 or newer
- Git installed and available in PATH
- Claude Code CLI installed and accessible
- A git repository with worktrees (optional, but recommended)

### Install from VSIX
1. Download the `.vsix` file from the releases
2. Open VS Code
3. Go to Extensions view (`Ctrl+Shift+X`)
4. Click the "..." menu and select "Install from VSIX..."
5. Select the downloaded `.vsix` file

### Install from Source
1. Clone this repository
2. Run `npm install` to install dependencies
3. Run `npm run compile` to build the extension
4. Press `F5` to run the extension in a new Extension Development Host window

## Usage

### Quick Start
1. Open a git repository with worktrees in VS Code
2. Open the Command Palette (`Ctrl+Shift+P`)
3. Run `Gadugi: Bloom` to create terminals and start Claude in all worktrees
4. Check the **Gadugi** panel in the sidebar to monitor processes

### Bloom Command Usage
```
1. Press Ctrl+Shift+P (Cmd+Shift+P on Mac)
2. Type "Bloom" and select the command
3. Wait for terminals to be created and Claude instances to start
4. Check the output for any errors or issues
```

### Monitor Panel Usage
1. **View Worktrees**: See all git worktrees with their current branch and status
2. **Monitor Processes**: Track Claude Code processes with live runtime duration
3. **Quick Actions**: 
   - Click 🔄 to refresh data
   - Right-click worktrees for context menu options
   - Click ⚡ to launch Claude in a specific worktree
   - Click 🛑 to terminate a specific process

### Available Commands

| Command | Description |
|---------|-------------|
| `Gadugi: Bloom` | Create terminals for all worktrees and start Claude |
| `Gadugi: Refresh` | Refresh the monitor panel data |
| `Gadugi: Launch Claude` | Start Claude in a specific worktree |
| `Gadugi: Terminate Process` | Stop a specific Claude process |
| `Gadugi: Navigate to Worktree` | Open worktree folder |
| `Gadugi: Show Output` | Show extension logs |
| `Gadugi: Show Info` | Display extension information |
| `Gadugi: Validate Setup` | Check prerequisites and setup |
| `Gadugi: Quick Start` | Run Bloom + show monitor panel |

## Configuration

The extension can be configured through VS Code settings:

```json
{
  "gadugi.updateInterval": 3000,
  "gadugi.claudeCommand": "claude --resume",
  "gadugi.showResourceUsage": true
}
```

### Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `gadugi.updateInterval` | `3000` | Update interval for process monitoring (milliseconds) |
| `gadugi.claudeCommand` | `"claude --resume"` | Command to execute when starting Claude Code |
| `gadugi.showResourceUsage` | `true` | Show memory usage information for processes |

## Screenshots

### Bloom Command in Action
```
🌸 Bloom: Setting up Claude terminals for all worktrees
├── 🔍 Discovering git worktrees... (3 found)
├── 🖥️ Creating terminal for main...
├── 🖥️ Creating terminal for feature-branch...
├── 🖥️ Creating terminal for hotfix-123...
└── ✅ Bloom completed! 3 terminals created, 3 Claude instances started
```

### Monitor Panel View
```
📁 Worktrees (3)
├── 🏠 main (main)
│   └── ⚡ Claude: 1234 (Running)
├── 🌿 feature-branch (feature-branch)  
│   └── ⚡ Claude: 5678 (Running)
└── 🔧 hotfix-123 (hotfix-123)
    └── ❌ No Claude process

⚡ Claude Processes (2)
├── 🟢 claude --resume (PID: 1234)
│   ├── ⏱️ Runtime: 02:34:12
│   ├── 📁 Worktree: main
│   └── 💾 Memory: 45.2 MB
└── 🟢 claude --resume (PID: 5678)
    ├── ⏱️ Runtime: 00:45:33
    ├── 📁 Worktree: feature-branch
    └── 💾 Memory: 38.7 MB
```

## Architecture

### Key Components
- **GitService**: Handles git worktree discovery and operations
- **TerminalService**: Manages VS Code terminal creation and execution
- **ClaudeService**: Integrates with Claude Code CLI
- **ProcessUtils**: Cross-platform process monitoring
- **MonitorPanel**: Real-time UI updates and tree view management
- **UpdateManager**: Coordinated refresh cycles with configurable intervals

### Cross-Platform Support
- **Windows**: Uses `tasklist` for process monitoring
- **macOS/Linux**: Uses `ps` for process monitoring  
- **Path Handling**: Automatic platform-specific path normalization
- **Shell Integration**: Platform-appropriate shell and terminal handling

## Development

### Building
```bash
npm install       # Install dependencies
npm run compile   # Compile TypeScript
npm run watch     # Watch for changes
```

### Testing
```bash
npm run test              # Run all tests
npm run test:unit         # Run unit tests only
npm run test:integration  # Run integration tests only
npm run test:coverage     # Run tests with coverage
```

### Linting
```bash
npm run lint      # Run ESLint
```

### Packaging
```bash
npm run package   # Create .vsix file
```

## Troubleshooting

### Common Issues

#### "No workspace folder is open"
- **Solution**: Open a folder in VS Code before using the extension

#### "Git is not installed or not in PATH"
- **Solution**: Install Git and ensure it's available in your system PATH

#### "Claude Code is not installed"
- **Solution**: Install Claude Code CLI and verify with `claude --version`

#### "No git worktrees found"
- **Solution**: Create worktrees using `git worktree add <path> <branch>`

#### "Failed to create terminal"
- **Solution**: Check VS Code terminal settings and permissions

### Debug Information

Use `Gadugi: Show Output` to view detailed logs including:
- Git command execution results
- Process discovery details
- Terminal creation status
- Error stack traces
- Performance metrics

### Validation Command

Run `Gadugi: Validate Setup` to check:
- ✅ VS Code version compatibility
- ✅ Workspace folder availability  
- ✅ Git installation and repository status
- ✅ Claude Code CLI accessibility
- ✅ Terminal creation capabilities

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow TypeScript best practices
- Add tests for new functionality
- Update documentation for user-facing changes
- Use the existing error handling patterns
- Follow VS Code extension development guidelines

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📝 **Issues**: Report bugs and request features on GitHub
- 📚 **Documentation**: Check this README and inline code documentation
- 🔍 **Debugging**: Use `Gadugi: Show Output` for detailed logs
- 💬 **Discussions**: Join the project discussions on GitHub

## Changelog

### v0.1.0 (Initial Release)
- ✨ Implemented Bloom command for automated terminal and Claude setup
- ✨ Added real-time monitor panel with worktree and process tracking
- ✨ Cross-platform support for Windows, macOS, and Linux
- ✨ Comprehensive error handling and user feedback
- ✨ Configurable update intervals and Claude commands
- ✨ Complete test suite with >90% coverage
- 📚 Full documentation and usage examples

## Related Projects

- **Gadugi**: Multi-agent development system
- **Claude Code**: AI-powered code assistant CLI
- **Git Worktree**: Git's parallel development feature

---

**Made with ❤️ for the Gadugi multi-agent development ecosystem**