@echo off
chcp 65001 >nul
echo ========================================================
echo  🌸 Lili IA — Motor Inteligente de Pré-Vendas Imobiliárias
echo  Iniciando Console Web (GroqCloud + WhatsApp QR Code)
echo ========================================================
echo.
echo Abrindo o navegador em http://127.0.0.1:8000/ ...
start http://127.0.0.1:8000/
echo.
python run_server.py
pause
