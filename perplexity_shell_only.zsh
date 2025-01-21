#!/usr/bin/env zsh

## Basic Perplexity ZSH plugin

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

    local file="$1"

    # Contrived example for testing
    local question="${2:-What is this file and what does it do?}"
    
    if [[ ! -f "$file" ]]; then
        echo "File not found: $file"
        return 1
    fi

    # Get file metadata
    local file_type=$(file -b "$file")
    local file_size=$(ls -lh "$file" | awk '{print $5}')
    local created_date=$(stat -f "%Sc" "$file" 2>/dev/null || stat -c "%y" "$file")

    # Prepare the prompt
    local prompt="File: ${file}
      Type: ${file_type}
      Size: ${file_size}
      Created: ${created_date}

      Question: ${question}

      Please provide relevant information about this file."

    # Make API call to Perplexity
    curl -s -X POST "https://api.perplexity.ai/chat/completions" \
        -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"llama-3.1-sonar-small-128k-online\",
            \"messages\": [{
                \"role\": \"user\",
                \"content\": \"${prompt}\"
            }]
        }" | jq -r '.choices[0].message.content'
}

# Function to get help about a command
pxhelp() {
    if [[ $# -eq 0 ]]; then
        echo "Usage: pxhelp <command> [specific question]"
        return 1
    fi

    local command="$1"
    local question="${2:-How do I use this command and what are its common use cases?}"

    # Get command type and location of the man page, which we may want to include as context
    local cmd_type=$(type "$command" 2>/dev/null)
    local man_exists=$(man -w "$command" 2>/dev/null)

    # If added, will request a JSON-formatted response
    local response_schema='{"type":"json_schema","json_schema":{"schema":{"type":"object","properties":{"explanation":{"type":"string","description":"Main explanation text"},"examples":{"type":"array","items":{"type":"string"},"description":"List of examples or key points"}},"required":["explanation","examples"]}}}'

    # Debugging JSON decode error
    local escaped_cmd_type=$(echo "$cmd_type" | sed 's/"/\\"/g' | sed ':a;N;$!ba;s/\n/\\n/g')
    local escaped_question=$(echo "$question" | sed 's/"/\\"/g')
    local escaped_command=$(echo "$command" | sed 's/"/\\"/g')

    # Prompt to send
     local prompt="Command: ${escaped_command}
      Command type: ${escaped_cmd_type}
      Man page exists: ${man_exists:+yes}${man_exists:-no}

      Question: ${escaped_question}

      Please provide a clear explanation and practical examples."

    # Make API call to Perplexity
    curl -s -X POST "https://api.perplexity.ai/chat/completions" \
        -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"llama-3.1-sonar-small-128k-online\",
            \"messages\": [{
                \"role\": \"system\",
                \"content\": \"Provide clear, structured responses with an explanation and practical examples.\"
            },
            {
                \"role\": \"user\",
                \"content\": \"${prompt}\"
            }]
        }" | jq '.'

}

# For dev only, remove before publish
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