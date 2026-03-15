@echo off
echo ===================================================
echo  Analizador de Resultados del Experimento
echo ===================================================
echo.
echo Generando graficas y reporte...
python -m metrics.analyzer
echo.
echo Revisa la carpeta 'charts/' para ver los resultados.
pause
