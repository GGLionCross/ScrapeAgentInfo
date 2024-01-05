@ECHO OFF

REM make.bat is designed to replicated make functionality or npm scripts

REM Local Workplace Commands
if %1 EQU app .env\Scripts\python.exe main.py

REM Remind user of available functions
IF %1 EQU --help (
  ECHO --------------
  ECHO AVAILABLE ARGS
  ECHO --------------
  ECHO app
  ECHO --------------
)