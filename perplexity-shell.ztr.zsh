#! /usr/bin/env zsh

# Load zsh-test-runner
#ztr_path="${ZTR_PATH:${0:A:h}/../zsh-test-runner/ztr.zsh}"
ztr_path="/opt/homebrew/Cellar/zsh-test-runner/2.1.1/share/zsh-test-runner/ztr.zsh"
. "${ztr_path}" || { echo "Failed to load zsh-test-runner" >&2; exit 1; }

SCRIPT_DIR="${0:A:h}"
. "${SCRIPT_DIR}/perplexity-shell.zsh"

ztr clear-summary

ztr test '[[ -n "${SCRIPT_DIR}" ]]' 'SCRIPT_DIR is set' 'Required for script operation'

# Setup test suite
ZTR_SETUP_FN() {
    export PERPLEXITY_API_KEY="test-api-key"
#    unset ZSH_DEBUG ZSHDB_FILE _Dbg_shell_temp_profile
#    local TEST_DIR="${0:A:h}"
}


# Test cases

#ztr test '[[ -n "$SCRIPT_DIR" ]]' \
#  "Script directory detection" \
#  "Should set SCRIPT_DIR when debugged" \
#  --emulate -LR zsh <<<'
#  ZSH_DEBUG=1
#  source perplexity-shell.zsh debug "${TEST_DIR}/perplexity-shell.zsh"
#  '
#
#ztr test '[[ -n "${PERPLEXITY_API_KEY}" ]]' \
#  'PERPLEXITY_API_KEY is set' \
#  --emulate -LR zsh <<<'
#  PERPLEXITY_API_KEY=""
#  source perplexity-shell.zsh px "test query"
#  '

#ztr test '[[ -n "$SCRIPT_DIR" ]]' \
#  "Direct execution detection" \
#  "Should set SCRIPT_DIR from ZSH_SCRIPT" <<< '
#  ZSH_SCRIPT="${TEST_DIR}/perplexity-shell.zsh"
#  source perplexity-shell.zsh px "test query"
#  '

ztr test '[[ -n "${PERPLEXITY_API_KEY}" ]]' 'PERPLEXITY_API_KEY is set'

PERPLEXITY_API_KEY=""
ztr test '! px "test query" 2>/dev/null' 'px fails when PERPLEXITY_API_KEY is empty'

ztr test '! is_being_debugged' 'Debug mode is not active by default'
ZSH_DEBUG=1
ztr test 'is_being_debugged' 'Debug mode detected with ZSH_DEBUG'
unset ZSH_DEBUG

ZSHDB_FILE=1
ztr test 'is_being_debugged' 'Debug mode is detected with ZSHDB_FILE'
unset ZSHDB_FILE

_Dbg_shell_temp_profile=1
ztr test 'is_being_debugged' 'Debug mode detected with _Dbg_shell_temp_profile'
unset _Dbg_shell_temp_profile

ztr test 'px "test query" --debug 2>/dev/null' 'px accepts debug flag'