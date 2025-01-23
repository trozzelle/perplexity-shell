#!/usr/bin/env zsh

## Basic Perplexity ZSH plugin
# This script uses a python script for the heavy lifting (parsing, request, and response formatting)

# Check if PERPLEXITY_API_KEY is set
if [[ -z "${PERPLEXITY_API_KEY}" ]]; then
    echo "Please set PERPLEXITY_API_KEY in your environment variables"
    return 1
fi

# Function to ask about the context of a file
pxcontext() {
    if [[ $# -eq 0 ]]; then
        echo "Usage: pxcontext <file_path> [question]"
        return 1
    fi

    # Contrived example for testing
    local file="$1"
    local question="${2:-What is this file and what does it do?}"

    if [[ ! -f "$file" ]]; then
        echo "File not found: $file"
        return 1
    fi

    # Get file metadata
    local file_type=$(file -b "$file")
    local file_size=$(ls -lh "$file" | awk '{print $5}')
    local created_date=$(stat -f "%Sc" "$file" 2>/dev/null || stat -c "%y" "$file")

  # Make call to python interpreter and handle call logic more robustly in perplexity_query.py
  python3 "${0:A:h}/perplexity_query.py" \
  --query "Where is this file from? (File: $file)" \
  --mode "file_info" \
  --file_type "${file_type}"
  --file_size "${file_size}"
  --file_created "${created_date}"
}

pxhelp() {
    if [[ $# -eq 0 ]]; then
        echo "Usage: pxhelp <command> [specific question]"
        return 1
    fi

    local command="$1"
    local question="${2:-How do I use this command and what are its common use cases?}"

    # Get command type and location
    local cmd_type=$(type "$command" 2>/dev/null)
    local man_exists=$(man -w "$command" 2>/dev/null)


  python3 "${0:A:h}/perplexity_query.py" \
  --query "How can I use the '$cmd' command effectively?" \
  --api_key "${PERPLEXITY_API_KEY}" \
  --mode "cmd_help" \
  --cmd_type "${cmd_type}" \
  --man_exists "${man_exists}"

}

## Just for dev purposes, remove before publish
#if [[ -z "${ZSH_EVAL_CONTEXT}" || "${ZSH_EVAL_CONTEXT}" == "toplevel" ]]; then
command="$1"
shift

case $command in
  "pxhelp")
    pxhelp "$@"
    ;;
  "pxcontext")
    pxcontext "$@"
    ;;
  *)
    echo "Usage $0 <pxhelp|pxcontext> [arguments...]"
    exit 1
    ;;
esac
#fi

compctl -g '*.*' pxcontext
compctl -g '' pxhelp