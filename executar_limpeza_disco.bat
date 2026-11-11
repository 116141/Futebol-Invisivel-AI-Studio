@echo off
chcp 65001 >nul
echo ========================================================
echo   LIMPANDO TEMPORARIOS E LIBERANDO DISCO C:
echo ========================================================
python limpar_temporarios.py
echo.
echo Concluido!
pause
