@echo off
title "AI Studio - Futebol e Alana Cruz Moda"
cd /d "C:\Users\Uni-CvFCT-EdmilsonGi\Documents\projectoD\money"

echo ========================================================
echo        INICIANDO AI STUDIO (FUTEBOL + MODA)
echo ========================================================
echo.
echo Abrindo navegador em http://127.0.0.1:8505 ...
start http://127.0.0.1:8505

echo.
echo Servidor rodando... Para fechar, basta fechar esta janela.
echo ========================================================
.\.venv\Scripts\python.exe app_render_studio.py
pause
