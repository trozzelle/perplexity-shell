#!/usr/bin/env zsh

if [[ -z "${PERPLEXITY_API_KEY}" ]]; then
    echo "Please set PERPLEXITY_API_KEY in your environment variables"
    return 1
fi

px() {
  if [[ $# -eq 0 ]]; then
    echo "Usage: px <search query>"
    return 1
  fi

  python3 "${0:A:h}/perplexity_shell.py" --query "$*"
}


_px() {
  _arguments '1:search query'
}

command="$1"
shift

case $command in
  "px")
    px "$@"
    ;;
  *)
    echo "Usage $0 Usage: px <search query>"
    exit 1
    ;;
esac