"""
API Gateway con Rate Limiting basado en JWT (user_id)

HIPÓTESIS ARQUITECTÓNICA:
"El uso de rate limiting basado en identidad del usuario en el API Gateway
mejora la protección contra ataques de denegación de servicio distribuidos
en arquitecturas de microservicios."

Este API Gateway implementa rate limiting por user_id extraído del JWT,
lo que previene bypass mediante múltiples IPs.
"""
from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from jose import jwt, JWTError
from datetime import datetime
import redis
import time
import json

app = Flask(__name__)
api = Api(app)

# Redis para almacenar contadores y métricas
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
metrics_client = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

# Cargar clave pública para validar JWT
PUBLIC_KEY = None

def load_public_key():
    global PUBLIC_KEY
    try:
        with open('tokens.json', 'r') as f:
            data = json.load(f)
            PUBLIC_KEY = data.get('public_key')
    except:
        from api_gateway.auth import PUBLIC_KEY as pk
        PUBLIC_KEY = pk

load_public_key()

def get_user_id_from_jwt():
    """
    Extrae user_id del token JWT para rate limiting.

    Esta es la función clave del experimento:
    - Un atacante con múltiples IPs pero el MISMO user_id
      será limitado por su identidad, no por su IP.
    """
    auth_header = request.headers.get('Authorization', '')

    if not auth_header.startswith('Bearer '):
        # Sin token: usar IP como fallback (vulnerable)
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        record_metric('requests_without_jwt', client_ip)
        return f"ip:{client_ip}"

    token = auth_header.replace('Bearer ', '')

    try:
        if PUBLIC_KEY is None:
            load_public_key()

        payload = jwt.decode(token, PUBLIC_KEY, algorithms=['RS256'])
        user_id = payload.get('user_id', 'unknown')
        record_metric('requests_with_jwt', user_id)
        return f"user:{user_id}"

    except JWTError as e:
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        record_metric('invalid_jwt_attempts', client_ip)
        return f"ip:{client_ip}"

def record_metric(metric_name: str, identifier: str):
    """Registra métricas en Redis para análisis posterior"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    key = f"metric:{metric_name}:{datetime.now().strftime('%Y%m%d%H%M')}"
    metrics_client.hincrby(key, identifier, 1)
    metrics_client.expire(key, 3600)  # TTL 1 hora

def record_request_result(user_id: str, blocked: bool, ip: str):
    """Registra resultado de request para métricas del experimento"""
    timestamp = datetime.now().isoformat()
    result = {
        'timestamp': timestamp,
        'user_id': user_id,
        'ip': ip,
        'blocked': blocked
    }
    metrics_client.rpush('experiment:requests', json.dumps(result))

    # Contadores agregados
    if blocked:
        metrics_client.incr('experiment:blocked_total')
        metrics_client.incr(f'experiment:blocked:{user_id}')
    else:
        metrics_client.incr('experiment:accepted_total')
        metrics_client.incr(f'experiment:accepted:{user_id}')

# Rate limiter usando JWT user_id
limiter = Limiter(
    app=app,
    key_func=get_user_id_from_jwt,
    storage_uri="redis://localhost:6379/0",
    strategy="fixed-window"
)

@app.errorhandler(429)
def rate_limit_exceeded(e):
    """Handler para cuando se excede el rate limit"""
    user_key = get_user_id_from_jwt()
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    record_request_result(user_key, blocked=True, ip=client_ip)

    return jsonify({
        'error': 'Rate limit exceeded',
        'message': 'Too many requests. Please try again later.',
        'rate_limited_by': 'user_id' if user_key.startswith('user:') else 'ip',
        'retry_after': 60
    }), 429

class AccommodationSearchResource(Resource):
    """
    Endpoint de búsqueda de hospedajes
    Rate limit: 100 requests/minuto por user_id
    """
    decorators = [limiter.limit("100 per minute")]

    def get(self, accommodation_id):
        start_time = time.time()

        user_key = get_user_id_from_jwt()
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

        # Registrar request exitoso
        record_request_result(user_key, blocked=False, ip=client_ip)

        latency_ms = (time.time() - start_time) * 1000

        # Simular respuesta del SearchService
        return {
            'id': accommodation_id,
            'name': f'Accommodation {accommodation_id}',
            'status': 'available',
            'rate_limited_by': 'user_id' if user_key.startswith('user:') else 'ip',
            'served_by': 'api_gateway',
            'latency_ms': round(latency_ms, 2),
            'client_ip': client_ip
        }, 200

class HealthResource(Resource):
    def get(self):
        return {'status': 'healthy', 'service': 'API Gateway'}, 200

class MetricsResource(Resource):
    """Endpoint para obtener métricas del experimento"""
    def get(self):
        blocked = int(metrics_client.get('experiment:blocked_total') or 0)
        accepted = int(metrics_client.get('experiment:accepted_total') or 0)
        total = blocked + accepted

        return {
            'total_requests': total,
            'accepted_requests': accepted,
            'blocked_requests': blocked,
            'block_rate': round(blocked / total * 100, 2) if total > 0 else 0,
            'effectiveness': 'High' if blocked > accepted * 0.5 else 'Low'
        }, 200

class ResetMetricsResource(Resource):
    """Resetear métricas para nuevo experimento"""
    def post(self):
        keys = metrics_client.keys('experiment:*')
        for key in keys:
            metrics_client.delete(key)
        return {'status': 'metrics_reset'}, 200

api.add_resource(AccommodationSearchResource, '/api/accommodations/<int:accommodation_id>')
api.add_resource(HealthResource, '/api/health')
api.add_resource(MetricsResource, '/api/metrics')
api.add_resource(ResetMetricsResource, '/api/metrics/reset')

if __name__ == '__main__':
    print("=== API Gateway - Experimento Rate Limiting JWT ===")
    print("Hipótesis: Rate limiting por user_id previene DDoS distribuido")
    print("Endpoint: /api/accommodations/<id>")
    print("Rate Limit: 100 requests/minuto por user_id")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
