@echo off
echo ===================================================
echo  Simulador de Ataque DDoS Distribuido
echo ===================================================
echo.
echo Este script simula un ataque DDoS desde multiples IPs
echo para evaluar la efectividad del rate limiting.
echo.
echo Asegurate de que:
echo  1. Redis este corriendo (docker start redis)
echo  2. API Gateway este corriendo (run_api_gateway.bat)
echo  3. Los tokens esten generados (generate_tokens.bat)
echo.
pause
python -m ddos_simulator.distributed_attack
pause
