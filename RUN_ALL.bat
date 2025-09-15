@echo off
setlocal
cd /d %~dp0
where python >nul 2>nul && (set PYBIN=python) || (set PYBIN=py)
%PYBIN% heartcore_launcher.py --smart-batch --stagger 1 --session heartcore
