# Travel Hub - Experimento 1: Redundancia Activa

Arquitectura de microservicios con API Gateway, SearchService (3 réplicas) y Heartbeat Monitor.

## Estructura del Proyecto

```
experimento_1/
├── api_gateway/          # API Gateway (punto de entrada)
├── search_service/       # Microservicio de búsqueda
├── heartbeat_monitor/    # Monitor de salud
├── run_instance_*.bat    # Scripts para cada réplica
└── requirements.txt
```

## Requisitos Previos

1. **Python 3.8+**
2. **Redis** corriendo en localhost:6379

### Instalar Redis (Windows)

**Opción Docker:**
```bash
docker run -d --name redis -p 6379:6379 redis
```

## Instalación

```bash
cd "C:\Users\KATANA\Documents\Master\Ciclo 3\Arquitecturas agiles\experimento_1"
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Poblar Base de Datos

```bash
.\seed_database.bat
```

O manualmente:
```bash
python -m search_service.seed_db
```

## Ejecutar el Sistema (5 terminales)

### Terminal 1: Redis (si usas Docker)
```bash
docker start redis
```

### Terminal 2: API Gateway
```bash
.\venv\Scripts\activate
.\run_api_gateway.bat
```

### Terminal 3, 4, 5: Las 3 Réplicas del SearchService

**Terminal 3:**
```bash
.\venv\Scripts\activate
.\run_instance_1.bat
```

**Terminal 4:**
```bash
.\venv\Scripts\activate
.\run_instance_2.bat
```

**Terminal 5:**
```bash
.\venv\Scripts\activate
.\run_instance_3.bat
```

### Terminal 6: Heartbeat Monitor
```bash
.\venv\Scripts\activate
.\run_heartbeat.bat
```

## Probar el API

```bash
# Obtener hospedaje por ID
curl http://localhost:5000/api/accommodation/1
curl http://localhost:5000/api/accommodation/500

# Health check del gateway
curl http://localhost:5000/api/health
```

## Probar Indisponibilidad de Réplicas

### Escenario 1: Simular caída de una instancia
1. Con las 3 instancias corriendo, observa el Heartbeat Monitor
2. Presiona `Ctrl+C` en la Terminal 3 (Instance 1)
3. El Heartbeat Monitor mostrará: `ALERT: Instance 1 is DOWN!`
4. Las requests seguirán funcionando porque Instance 2 y 3 están activas

### Escenario 2: Simular caída de dos instancias
1. Detén Instance 1 y Instance 2 (Ctrl+C en Terminal 3 y 4)
2. El sistema sigue funcionando con Instance 3
3. Observa en las respuestas: `"served_by_instance": "3"`

### Escenario 3: Recuperación
1. Reinicia Instance 1: `.\run_instance_1.bat`
2. El Heartbeat Monitor mostrará: `Instance 1 is back UP!`

## Verificar qué instancia responde

Cada respuesta incluye `served_by_instance` indicando cuál réplica procesó la solicitud:

```json
{
  "id": 1,
  "name": "Hotel Example",
  "served_by_instance": "2"
}
```

## Arquitectura

```
                    ┌─────────────────┐
                    │   API Gateway   │
                    │   (Port 5000)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  QueriesQueue   │
                    │    (Redis)      │
                    └────────┬────────┘
           ┌─────────────────┼─────────────────┐
           │                 │                 │
    ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
    │ Instance 1  │   │ Instance 2  │   │ Instance 3  │
    │ SearchSvc   │   │ SearchSvc   │   │ SearchSvc   │
    └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │
                    ┌────────▼────────┐
                    │   SQLite DB     │
                    │ (travel_hub.db) │
                    └─────────────────┘

    ┌─────────────────┐
    │ Heartbeat Mon.  │◄────── HealthQueue (cada 5s)
    └─────────────────┘
```
