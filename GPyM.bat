@echo off
if exist MAIN.py (
rem
) else (
echo %CD%にはMAIN.pyが存在しません
set /p __=
exit /b
)
echo on
py MAIN.py