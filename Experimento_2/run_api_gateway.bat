@echo off
echo ===================================================
echo  API Gateway - Experimento Rate Limiting JWT
echo ===================================================
echo.
echo Hipotesis: Rate limiting por user_id previene DDoS
echo Endpoint: /api/accommodations/{id}
echo Rate Limit: 100 requests/minuto por user_id
echo.
flask run --port=5000
