@echo off
if exist BUNKATSU_ONLY.py (
rem
) else (
echo %CD%�ɂ�BUNKATSU_ONLY.py�����݂��܂���
set /p __=
exit /b
)
echo on
py BUNKATSU_ONLY.py