# Travel Hub - Experimento 2: Rate Limiting contra DDoS Distribuido

## Hipótesis Arquitectónica

> **"El uso de rate limiting basado en identidad del usuario en el API Gateway mejora la protección contra ataques de denegación de servicio distribuidos en arquitecturas de microservicios."**

## Diseño del Experimento

### Objetivo
Validar que el rate limiting basado en `user_id` (extraído del JWT) es más efectivo que el rate limiting por IP para proteger contra ataques DDoS donde el atacante usa múltiples direcciones IP (botnet).

### Métricas a Medir
1. **Requests bloqueados por atacante** - Métrica principal
2. **Requests exitosos del atacante** - Indicador de bypass
3. **Tasa de bloqueo (%)** - Efectividad del control
4. **Latencia promedio** - Overhead del control

### Simulación del Ataque Distribuido
- **Botnet simulada:** 10 IPs diferentes
- **Requests por IP:** 50-100
- **Total de requests:** 500-1000
- **Objetivo:** Bypass del rate limit de 100 req/min

### Evaluación de Efectividad
| Tasa de Bloqueo | Evaluación |
|-----------------|------------|
| ≥ 80% | EFECTIVO - El control previene el ataque |
| 50-79% | PARCIALMENTE EFECTIVO - Requiere ajustes |
| < 50% | INEFECTIVO - El atacante logra bypass |

## Estructura del Proyecto

```
experimento_2/
├── api_gateway/
│   ├── __init__.py
│   ├── app.py              # API Gateway con rate limiting JWT
│   ├── auth.py             # Generador de tokens JWT
│   └── config.py           # Configuración
├── ddos_simulator/
│   ├── __init__.py
│   └── distributed_attack.py  # Simulador de ataque DDoS
├── metrics/
│   ├── __init__.py
│   └── analyzer.py         # Analizador y generador de gráficas
├── tests/
│   └── test_rate_limiting.py
├── app.py                  # Entry point (flask run)
├── requirements.txt
├── run_api_gateway.bat
├── generate_tokens.bat
├── run_ddos_simulation.bat
├── analyze_results.bat
└── README.md
```

## Requisitos Previos

1. **Python 3.8+**
2. **Redis** corriendo en localhost:6379

### Instalar Redis (Docker)
```bash
docker run -d --name redis -p 6379:6379 redis
```

## Instalación

```bash
cd "C:\Users\KATANA\Documents\Master\Ciclo 3\Arquitecturas agiles\experimento_2"
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución del Experimento

### Paso 1: Iniciar Redis
```bash
docker start redis
```

### Paso 2: Generar Tokens JWT
```bash
.\venv\Scripts\activate
.\generate_tokens.bat
```
Esto crea `tokens.json` con tokens para atacantes y usuarios legítimos.

### Paso 3: Iniciar API Gateway (Terminal 1)
```bash
.\venv\Scripts\activate
flask run
```

### Paso 4: Ejecutar Simulación de Ataque (Terminal 2)
```bash
.\venv\Scripts\activate
.\run_ddos_simulation.bat
```

El simulador ejecutará automáticamente:
1. **Escenario 1:** Ataque SIN JWT (rate limiting por IP)
2. **Espera de 60 segundos** para resetear rate limits
3. **Escenario 2:** Ataque CON JWT (rate limiting por user_id)

### Paso 5: Analizar Resultados
```bash
.\analyze_results.bat
```

Genera:
- `charts/comparison_chart.png` - Gráfica comparativa
- `charts/effectiveness_chart.png` - Gráfica de efectividad
- `charts/experiment_report.txt` - Reporte detallado

## Resultados Esperados

### Escenario 1: Rate Limiting por IP (Vulnerable)
```
Atacante con 10 IPs → 10 x 100 req/min = 1000 req/min permitidos
Resultado esperado: ~95% requests aceptados (BYPASS EXITOSO)
```

### Escenario 2: Rate Limiting por JWT (Protegido)
```
Atacante con 10 IPs pero MISMO user_id → 100 req/min total
Resultado esperado: ~80-90% requests bloqueados (BYPASS FALLIDO)
```

## Arquitectura

```
                    ┌─────────────────────────┐
                    │   Atacante (Botnet)     │
                    │   10 IPs diferentes     │
                    │   MISMO user_id (JWT)   │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │      API Gateway        │
                    │  ┌─────────────────┐    │
                    │  │ JWT Validator   │    │
                    │  │ (extraer user_id)│   │
                    │  └────────┬────────┘    │
                    │  ┌────────▼────────┐    │
                    │  │  Rate Limiter   │    │
                    │  │ (por user_id)   │    │
                    │  └────────┬────────┘    │
                    └───────────┼─────────────┘
                                │
                    ┌───────────▼─────────────┐
                    │        Redis            │
                    │  Contadores por user_id │
                    │  TTL: 60 segundos       │
                    └─────────────────────────┘
```

## Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/accommodations/<id>` | Búsqueda de hospedaje (rate limited) |
| GET | `/api/health` | Health check |
| GET | `/api/metrics` | Métricas del experimento |
| POST | `/api/metrics/reset` | Resetear métricas |

## Ejemplo de Uso

```bash
# Request con JWT (rate limited por user_id)
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/accommodations/1

# Ver métricas
curl http://localhost:5000/api/metrics
```

## Conclusiones Esperadas

1. **Rate limiting por IP es vulnerable** a ataques distribuidos
2. **Rate limiting por user_id (JWT) es efectivo** contra botnets
3. **Trade-off aceptable:** ~5-10ms de overhead por validación JWT
4. **Recomendación:** Implementar rate limiting por identidad en API Gateways

## Referencias

- TravelHub - Vista de Concurrencia (Rate Limiting + Thread Isolation)
- OWASP Rate Limiting Cheat Sheet
- RFC 7519 - JSON Web Tokens
