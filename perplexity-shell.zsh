#!/usr/bin/env zsh

## Returns true if script is being run via debugger
is_being_debugged() {
  [[ -n "${ZSH_DEBUG}" || -n "${ZSHDB_FILE}" || -n "${_Dbg_shell_temp_profile}" ]]
}

## If we're debugging, we get script dir from command line args
if is_being_debugged; then
  SCRIPT_DIR="${@: -1:1}"
  SCRIPT_DIR="${SCRIPT_DIR:A:h}"
## If run directly, ZSH_SCRIPT is populated
elif [[ -n "${ZSH_SCRIPT}" ]]; then
  SCRIPT_DIR="${ZSH_SCRIPT:A:h}"
## If being sourced, convert first arg to abs path and get dir
elif [[ -n "${0}" ]]; then
  SCRIPT_DIR="${0:A:h}"
else
  echo "Unable to determine script's directory"
  return 1
fi

if [[ -z "${PERPLEXITY_API_KEY}" ]]; then
    echo "Please set PERPLEXITY_API_KEY in your environment variables"
    return 1
fi

px() {
  if [[ $# -eq 0 ]]; then
    echo "Usage: px <search query>"
    return 1
  fi


  python3 "${SCRIPT_DIR}/perplexity_shell.py" --query "$*" $(is_being_debugged && echo "--debug")
}


if [[ "${ZSH_EVAL_CONTEXT}" == "toplevel" ]] || is_being_debugged; then

  if is_being_debugged && [[ $# -eq 0 ]]; then
      echo "Debug mode: no args provided"
      exit 0
  fi

  command="$1"
  shift

      case $command in
        "px")
            px "$@"
            ;;
        *)
            echo "Usage: $0 px <search query>"
            exit 1
            ;;
    esac
else
    if [[ -n "${ZSH_VERSION}" ]] && [[ "${-}" =~ "i" ]] && (( ${+functions[compdef]} )); then
        _px() {
            _arguments '1:search query:'
        }
        compdef _px px
    fi
fi


