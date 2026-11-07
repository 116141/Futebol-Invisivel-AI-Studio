@echo off
title "Autorizar Canal Futebol Invisivel - YouTube"
cd /d "C:\Users\Uni-CvFCT-EdmilsonGi\Documents\projectoD\money"

echo ========================================================
echo   AUTORIZAR UPLOAD DO YOUTUBE: FUTEBOL INVISIVEL
echo ========================================================
echo.
echo Esta prestes a abrir uma janela no navegador para fazer
echo login na conta Google que administra o canal Futebol Invisivel.
echo.
echo 1. Selecione a conta do Google correspondente
echo 2. Se aparecer aviso de 'App nao verificado', clique em:
echo    "Avancado" e depois "Aceder a Studio AutoViral (inseguro)"
echo 3. Marque a caixa para autorizar gerenciar videos do YouTube
echo 4. Conclua o login!
echo ========================================================
echo.
pause
.\.venv\Scripts\python.exe -c "from app.services import youtube_uploader; youtube_uploader.get_authenticated_service(canal_nome='futebol'); print('\n>>> SUCESSO! TOKEN DO FUTEBOL GRAVADO COM EXITO! <<<')"
echo.
pause
