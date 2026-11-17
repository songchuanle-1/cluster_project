@echo off
REM tick_full.bat <project> -- Task Scheduler entry: full pipeline tick (monitor + Codex design)
REM Task Scheduler runs with minimal PATH, so this sets a full PATH explicitly.
setlocal
set "PROJECT=%~1"
if "%PROJECT%"=="" echo Usage: %~nx0 ^<project^> && exit /b 1

set "PROJECT_ROOT=D:/project"
set "GIT_BASH=C:\Program Files (x86)\Git\bin\bash.exe"
set "GIT_USR=C:\Program Files (x86)\Git\usr\bin"
set "GIT_BIN=C:\Program Files (x86)\Git\bin"
set "NPM_BIN=%APPDATA%\npm"
set "CODEX_BIN_ROOT=%LOCALAPPDATA%\OpenAI\Codex\bin"

"%GIT_BASH%" -c "export PATH=\"%GIT_USR%:%GIT_BIN%:%NPM_BIN%:%CODEX_BIN_ROOT%:/usr/bin:/bin:$PATH\"; export PROJECT_ROOT=\"%PROJECT_ROOT%\"; export CODEX_PIPELINE_MODEL=\"${CODEX_PIPELINE_MODEL:-gpt-6-astra}\"; export CODEX_FALLBACK_MODEL=\"${CODEX_FALLBACK_MODEL:-deepseek-flash}\"; export CODEX_FRESH_THREAD=\"${CODEX_FRESH_THREAD:-1}\"; cd \"%PROJECT_ROOT%\"; bash \"%PROJECT_ROOT%/.claude/skills/songcl_research_pipeline/headless_tick_local.sh\" \"%PROJECT%\""
exit /b %ERRORLEVEL%
