#!/usr/bin/env zsh

## Basic Perplexity ZSH plugin
# This script tries to do everything within the shelll

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

    # Improved escaping
    local escaped_cmd_type=$(echo "$cmd_type" | perl -pe 's/\n/\\n/g' | perl -pe 's/"/\\"/g')
    local escaped_question=$(echo "$question" | perl -pe 's/"/\\"/g')
    local escaped_command=$(echo "$command" | perl -pe 's/"/\\"/g')

    # Create a single-line prompt with explicit \n characters
    local prompt="Command: ${escaped_command}\\nCommand type: ${escaped_cmd_type}\\nMan page exists: ${man_exists:+yes}${man_exists:-no}\\n\\nQuestion: ${escaped_question}\\n\\nPlease provide a clear explanation and practical examples."

    # Create the JSON payload as a single line
    local json_payload="{\"model\":\"sonar-pro\",\"messages\":[{\"role\":\"system\",\"content\":\"Provide clear, structured responses with an explanation and practical examples.\"},{\"role\":\"user\",\"content\":\"${prompt}\"}],\"max_tokens\": \"125\"}"


    local json_payload=$(cat <<EOF
    {
  "model": "sonar-pro",
  "messages": [
    {
      "role": "system",
      "content": "Provide clear, structured responses with an explanation and practical examples."
    },
    {
      "role": "user",
      "content": "${prompt}"
    }
  ],
  "max_tokens": "125"
}
EOF
)

  # Make request and store result in a temporary file
  local temp_file=$(mktemp)
   curl -s -X POST "https://api.perplexity.ai/chat/completions" \
        -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "$json_payload" > "$temp_file"

  #
  local escaped_json=$(jq -r '. | tojson' $temp_file | sed -e 's/^"//' -e 's/"$//')
  format_response "$escaped_json"


  rm "$temp_file"
  }


# Function to format the API response with colors and styling
format_response() {
    local json_response
    json_response="$*"

    # Define colors and styles
    local BLUE='\033[0;34m'
    local GREEN='\033[0;32m'
    local GRAY='\033[0;90m'
    local RESET='\033[0m'
    local BOLD='\033[1m'
    local CYAN='\033[0;36m'

    local choice=$(jq '.choices[0]' <<< $json_response 2>/dev/null)

    # Print a separator line
    echo "\n${BLUE}―――――――――――――――――――――――――――――――――――――――――――――${RESET}\n"

    # Process the content line by line to apply formatting
    local content=$(jq '.message.content' <<< "$choice" 2>/dev/null)
    echo "$content" | while IFS= read -r line; do
        # Format code blocks
        if [[ "$line" =~ ^'\`\`\`' ]]; then
            echo "${CYAN}$line${RESET}"
        # Format numbered lists
        elif [[ "$line" =~ ^[0-9]+\. ]]; then
            echo "${GREEN}$line${RESET}"
        else
            echo "$line"
        fi
    done

    local citations=$(jq -r '.citations[]' <<< "$json_response" 2>/dev/null | head -n 3)
    if [[ -n "$citations" ]]; then
        echo "\n${BOLD}References:${RESET}"
        echo "$citations" | while IFS= read -r citation; do
            echo "${GRAY}• $citation${RESET}"
        done
    fi

    # Print ending separator
    echo "\n${BLUE}―――――――――――――――――――――――――――――――――――――――――――――${RESET}\n"
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