@echo off
if exist MAIN.py (
rem
) else (
echo %CD%�ɂ�MAIN.py�����݂��܂���
set /p __=
exit /b
)
echo on
py MAIN.py