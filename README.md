# Perplexity Shell

A small zsh plugin that allows you to query Perplexity's search LLM from the command-line. Results are returned with citations and code examples, formatted for the terminal.

Currently WIP and unstable, and will be until v1.0.0.

## Features

- Rich terminal formatting with colored output and structured display
- Citation support with clickable links
- Code block syntax highlighting

## Prerequisites

- Python 3.11+
- ZSH shell
- Perplexity AI API key
- Required Python packages:
  - rich

## Installation

1. Clone the repository:
```bash
git clone https://github.com/trozzelle/perplexity-shell
cd perplexity-shell
```

2. Install dependencies:
```bash
pip install rich
```

3. Set up your Perplexity API key:
```bash
export PERPLEXITY_API_KEY="your-api-key-here"
```

4. Source the ZSH script in your `.zshrc`:
```bash
source /path/to/perplexity-shell.zsh
```

## Usage

### Basic Query
```bash
px "your query here"
```

### Debug Mode
```bash
px --debug "your query here"
```

### Direct Python Script Usage
```bash
python perplexity_shell.py --query "your query here" [--api_key YOUR_API_KEY] [--debug]
```

## Project Structure

- `perplexity_shell.py`: Main Python implementation
- `perplexity-shell.zsh`: ZSH integration script
- `logs/`: Directory for log files (automatically created)

