@echo off
if exist BUNKATSU_ONLY.py (
rem
) else (
echo %CD%にはBUNKATSU_ONLY.pyが存在しません
set /p __=
exit /b
)
echo on
py BUNKATSU_ONLY.py