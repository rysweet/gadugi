# Gadugi - Community Claude Code Agents

> **Gadugi** (gah-DOO-gee) - A Cherokee concept of communal work where community members come together to accomplish tasks that benefit everyone, sharing collective wisdom and mutual support.

## Overview

Gadugi is a centralized repository of reusable Claude Code agents and instructions, embodying the Cherokee philosophy of communal work and collective wisdom. This repository serves as the foundation for a distributed ecosystem of AI-powered development tools that can be shared across projects.

## Philosophy

The Cherokee concept of Gadugi represents:
- **ᎦᏚᎩ (Gadugi) - Communal Work**: Community members working together for mutual benefit
- **ᎠᏓᏅᏙ (Adanvdo) - Collective Wisdom**: Sharing knowledge for the greater good  
- **ᎠᎵᏍᏕᎸᏗ (Alisgelvdi) - Mutual Support**: Helping others knowing we all thrive together
- **ᎤᏂᎦᏚ (Unigadv) - Shared Resources**: Pooling tools and knowledge efficiently

This philosophy aligns perfectly with our vision of a shared agent repository where the Claude Code community contributes, maintains, and benefits from collective AI-powered development tools.

## Repository Structure

```
gadugi/
├── agents/                 # Reusable Claude Code agents
│   ├── workflow-master.md      # Orchestrates development workflows
│   ├── orchestrator-agent.md   # Manages parallel agent execution
│   ├── code-reviewer.md        # Automated code review
│   ├── prompt-writer.md        # Creates structured prompts
│   └── agent-manager.md        # Manages external agents
├── instructions/           # Generic Claude instructions
│   └── claude-generic-instructions.md
├── prompts/               # Reusable prompt templates
├── examples/              # Integration examples
└── docs/                  # Additional documentation
```

## Quick Start

### Using Gadugi in Your Project

1. **Configure Agent Manager** in your project:
   ```yaml
   # .claude/agent-manager/config.yaml
   repositories:
     - name: "gadugi"
       url: "https://github.com/rysweet/gadugi"
       type: "github"
       branch: "main"
   ```

2. **Import Instructions** in your CLAUDE.md:
   ```markdown
   @https://raw.githubusercontent.com/rysweet/gadugi/main/instructions/claude-generic-instructions.md
   ```

3. **Sync Agents** using Agent Manager:
   ```bash
   /agent:agent-manager install workflow-master
   ```

## Available Agents

### Workflow Management
- **workflow-master**: Orchestrates complete development workflows from issue to PR
- **orchestrator-agent**: Enables parallel execution of multiple agents

### Code Quality
- **code-reviewer**: Performs thorough code reviews on pull requests
- **code-review-response**: Processes and responds to code review feedback
- **prompt-writer**: Creates structured prompts for complex tasks

### Infrastructure
- **agent-manager**: Manages agent repositories and updates

## Contributing

We welcome contributions that embody the spirit of Gadugi:

1. **Fork** the repository
2. **Create** a feature branch
3. **Implement** your agent or improvement
4. **Test** thoroughly
5. **Submit** a pull request

### Contribution Guidelines

- Follow existing agent patterns and structure
- Include comprehensive documentation
- Add examples for complex agents
- Test your contributions
- Help review others' contributions

## Community

The Gadugi project thrives on community collaboration:

- **Share** your custom agents
- **Improve** existing agents
- **Document** best practices
- **Support** other developers

## Version Management

We use semantic versioning:
- **Major**: Breaking changes to agent interfaces
- **Minor**: New agents or features
- **Patch**: Bug fixes and improvements

## License

MIT License - See [LICENSE](LICENSE) for details

## Acknowledgments

- The Cherokee Nation for the inspiring concept of Gadugi
- The Claude Code community for continuous contributions
- Anthropic for enabling AI-powered development

---

*ᎤᎵᎮᎵᏍᏗ (Ulihelisdi) - "We are helping each other"*

Join us in building a thriving ecosystem of AI-powered development tools through the spirit of Gadugi.