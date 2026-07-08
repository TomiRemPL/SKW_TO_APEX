@echo off
setlocal

powershell -ExecutionPolicy Bypass -File "%~dp0kill-port.ps1"
