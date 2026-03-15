@echo off
echo Generando tokens JWT para el experimento...
python -m api_gateway.auth
echo.
echo Tokens guardados en tokens.json
pause
