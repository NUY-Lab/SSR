@echo off
if not exist scripts (
echo %CD%�ɂ�scripts�Ƃ������O�̃t�H���_�[�����݂��܂���
set /p __=
exit /b
)
if not exist BUNKATSU_ONLY.py (
echo %CD%\scripts�ɂ�BUNKATSU_ONLY.py�����݂��܂���
set /p __=
exit /b
)
echo on
py scripts\BUNKATSU_ONLY.py 