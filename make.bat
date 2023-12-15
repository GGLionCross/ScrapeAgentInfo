@ECHO OFF

REM make.bat is designed to replicated make functionality or npm scripts

REM Local Workplace Commands
if %1 EQU run py scrape-agent-info.py

REM Utility Commands
if %1 EQU show-clean-path ECHO %PATH:;=&echo.%

REM Remind user of available functions
IF %1 EQU --help (
  ECHO --------------
  ECHO AVAILABLE ARGS
  ECHO --------------
  ECHO run
  ECHO --------------
)