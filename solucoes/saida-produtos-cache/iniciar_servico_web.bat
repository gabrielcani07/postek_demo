@echo off
setlocal

cd /d "%~dp0"

set "APP_PORT=8080"
set "PRINT_MODE=raw9100"
set "POSTEK_PRINTER_HOST=192.168.1.21"
set "POSTEK_PRINTER_PORT=9100"
set "SAVE_PRINT_BATCH_FILES=0"

if not exist logs mkdir logs

echo Iniciando sistema web de saida de produtos...
echo Acesse: http://localhost:%APP_PORT%
echo Para parar, feche esta janela ou pressione Ctrl+C.
echo.

python app.py >> logs\servico-web.log 2>&1

echo.
echo O servidor foi encerrado. Veja logs\servico-web.log para detalhes.
pause
