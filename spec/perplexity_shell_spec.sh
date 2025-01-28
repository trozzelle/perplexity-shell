Describe 'perplexity-shell.zsh'
  BeforeRun 'PERPLEXITY_API_KEY=test_key' 'unset ZSH_DEBUG ZSHDB_FILE _Dbg_shell_temp_profile'

  It 'sets SCRIPT_DIR when debugged'
    When run script perplexity-shell.zsh debug /Users/ada.sh/Development/Projects/Perplexity-Shell/src/perplexity-shell.zsh
    The variable SCRIPT_DIR should be defined
    The variable SCRIPT_DIR should equal "/Users/ada.sh/Development/Projects/Perplexity-Shell/src"
  End

End