@echo off
REM tick_runner.bat <project> - compatibility wrapper for the unified pipeline tick
REM Usage: tick_runner.bat cluster_project
setlocal enabledelayedexpansion
set "PROJECT=%~1"
if "%PROJECT%"=="" echo Usage: %~nx0 ^<project^> && exit /b 1

set "PROJECT_ROOT=D:/project"
set "SKILL=%~dp0"
bash "%SKILL%/headless_tick_local.sh" "%PROJECT%"
exit /b %ERRORLEVEL%
