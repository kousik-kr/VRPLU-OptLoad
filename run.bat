@echo off
REM Windows batch script to run VRPLU-OptLoad
REM Usage: run.bat [additional arguments...]

setlocal enabledelayedexpansion

REM Get the current directory (workspace root)
set ROOT_DIR=%~dp0
set ROOT_DIR=%ROOT_DIR:~0,-1%

echo Checking dataset availability...
if exist "%ROOT_DIR%\scripts\download-dataset.sh" (
    echo Dataset check script found, but requires bash. Skipping...
) else (
    echo Warning: download-dataset.sh not found, skipping dataset check
)

echo.
echo Starting compilation and execution...
echo.

REM Change to src directory
cd /d "%ROOT_DIR%\src"

REM Compile all Java files
echo Compiling Java files...
javac *.java
if errorlevel 1 (
    echo Compilation failed!
    exit /b 1
)

echo Compilation successful!
echo Running VRPLoadingUnloadingMain...
echo.

REM Run the main Java program
java VRPLoadingUnloadingMain "%ROOT_DIR%" %*

endlocal
