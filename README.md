# Perplexity Shell

A small zsh plugin that allows you to get answers about a file or command. Currently WIP, this is being made to demo the capability of Perplexity's search LLM.  

## Features

- **File Context Analysis** (`pxcontext`): Get AI-powered insights about any file in your system
- **Command Help** (`pxhelp`): Receive detailed explanations and examples for any shell command


## Prerequisites

- Python 3.11+
- ZSH shell
- Perplexity API key
- Poetry (recommended for dependency management)
- Ruff (for code formatting and linting)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd perplexity-cli
```

2. Set up your environment:
```bash
# Create and activate virtual environment (optional)
python -m venv .venv
source .venv/bin/activate

# Install dependencies using Poetry
poetry install
```

3. Configure your API key:
```bash
export PERPLEXITY_API_KEY="your-api-key-here"
```

4. Add the ZSH functions to your shell:
```bash
# Add to your .zshrc
source /path/to/perplexity_python.zsh  # For Python-backed implementation
# OR
source /path/to/perplexity_shell_only.zsh  # For pure ZSH implementation
```

## Usage

### File Context Analysis
```bash
# Get information about a file
pxcontext path/to/file.txt

# Ask specific questions about a file
pxcontext path/to/file.txt "What are the main functions in this file?"
```

### Command Help
```bash
# Get general help for a command
pxhelp docker

# Ask specific questions about a command
pxhelp git "How do I revert a commit?"
```

