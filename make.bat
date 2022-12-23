@ECHO OFF

REM make.bat is designed to replicated make functionality or npm scripts

REM Local Workplace Commands
if %1 EQU run py scrape-agent-info.py

REM Virtual Enviornment Commands
REM   Make Virtual Environment For Python 3.10
if %1 EQU env-3x10 virtualenv .env -p C:\Users\lione\AppData\Local\Programs\Python\Python310\python.exe
REM   Make Virtual Environment For Python 3.11
if %1 EQU env-3x11 virtualenv .env -p C:\Users\lione\AppData\Local\Programs\Python\Python311\python.exe
if %1 EQU env-a .env\Scripts\activate
if %1 EQU env-d deactivate
REM   Copy installed packages to requirements.txt
if %1 EQU requirements pip freeze > requirements.txt
REM   Install from requirements.txt if on a new environment
if %1 EQU setup pip install -r requirements.txt
REM   Install python utils
if %1 EQU i-python-utils pip install -e ../../../Python
REM   Install selenium utils
if %1 EQU i-selenium-utils pip install -e ../../Selenium

REM Utility Commands
if %1 EQU show-clean-path ECHO %PATH:;=&echo.%

REM Remind user of available functions
IF %1 EQU --help (
  ECHO --------------
  ECHO AVAILABLE ARGS
  ECHO --------------
  ECHO upgrade-octoprint
  ECHO activate-env
  ECHO requirements
  ECHO setup
  ECHO --------------
)