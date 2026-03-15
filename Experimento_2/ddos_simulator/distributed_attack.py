"""
Simulador de Ataque DDoS Distribuido

PROPÓSITO:
Simular un ataque de denegación de servicio distribuido (DDoS) donde
un atacante usa múltiples IPs (botnet) para intentar bypass del rate limiting.

ESCENARIOS:
1. Ataque SIN JWT: Múltiples IPs, sin autenticación
2. Ataque CON JWT: Múltiples IPs, pero MISMO user_id en JWT

MÉTRICAS A CAPTURAR:
- Requests bloqueados por atacante
- Requests exitosos del atacante
- Efectividad del control (% bloqueado)
"""
import requests
import random
import time
import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import sys
import os

# Agregar path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_URL = "http://localhost:5000/api/accommodations"

class DDoSSimulator:
    def __init__(self, num_ips: int = 10, requests_per_ip: int = 100):
        """
        Args:
            num_ips: Número de IPs diferentes que simula el atacante (botnet)
            requests_per_ip: Requests a enviar desde cada IP
        """
        self.num_ips = num_ips
        self.requests_per_ip = requests_per_ip
        self.total_requests = num_ips * requests_per_ip

        self.results = {
            'accepted': 0,
            'blocked': 0,
            'errors': 0,
            'latencies': []
        }
        self.lock = threading.Lock()

        # Generar IPs falsas para simular botnet
        self.fake_ips = [
            f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
            for _ in range(num_ips)
        ]

    def generate_fake_ip(self) -> str:
        """Genera una IP aleatoria del 'botnet'"""
        return random.choice(self.fake_ips)

    def load_attacker_token(self) -> str:
        """Carga el token JWT del atacante"""
        try:
            with open('tokens.json', 'r') as f:
                data = json.load(f)
                return data['attacker']['attacker-001']
        except FileNotFoundError:
            print("⚠ tokens.json no encontrado. Generando tokens...")
            from api_gateway.auth import generate_attacker_tokens
            tokens = generate_attacker_tokens(1)
            return tokens['attacker-001']

    def send_request(self, ip: str, token: str = None) -> dict:
        """
        Envía una request simulando origen desde una IP específica

        Args:
            ip: IP a simular (X-Forwarded-For)
            token: JWT token (None para ataque sin autenticación)
        """
        start_time = time.time()
        accommodation_id = random.randint(1, 1000)

        headers = {'X-Forwarded-For': ip}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            response = requests.get(
                f"{API_URL}/{accommodation_id}",
                headers=headers,
                timeout=5
            )

            latency = (time.time() - start_time) * 1000

            with self.lock:
                self.results['latencies'].append(latency)

                if response.status_code == 200:
                    self.results['accepted'] += 1
                    return {'status': 'accepted', 'ip': ip, 'latency': latency}
                elif response.status_code == 429:
                    self.results['blocked'] += 1
                    return {'status': 'blocked', 'ip': ip, 'latency': latency}
                else:
                    self.results['errors'] += 1
                    return {'status': 'error', 'code': response.status_code}

        except Exception as e:
            with self.lock:
                self.results['errors'] += 1
            return {'status': 'error', 'message': str(e)}

    def run_attack_without_jwt(self):
        """
        ESCENARIO 1: Ataque sin JWT (rate limiting por IP)

        Expectativa: El atacante PUEDE hacer bypass usando múltiples IPs
        Cada IP tiene su propia quota de 100 req/min
        Total esperado: ~100% requests aceptados
        """
        print("\n" + "=" * 60)
        print("ESCENARIO 1: Ataque DDoS SIN JWT (Rate Limiting por IP)")
        print("=" * 60)
        print(f"Atacante simulando {self.num_ips} IPs diferentes")
        print(f"Requests por IP: {self.requests_per_ip}")
        print(f"Total requests: {self.total_requests}")
        print("-" * 60)

        self.results = {'accepted': 0, 'blocked': 0, 'errors': 0, 'latencies': []}

        with ThreadPoolExecutor(max_workers=self.num_ips) as executor:
            futures = []

            for ip in self.fake_ips:
                for _ in range(self.requests_per_ip):
                    futures.append(executor.submit(self.send_request, ip, None))

            for i, future in enumerate(as_completed(futures)):
                if (i + 1) % 100 == 0:
                    print(f"  Progreso: {i + 1}/{self.total_requests} requests enviados")

        return self._generate_report("SIN_JWT")

    def run_attack_with_jwt(self):
        """
        ESCENARIO 2: Ataque con JWT (rate limiting por user_id)

        Expectativa: El atacante NO puede hacer bypass
        Todas las IPs comparten el mismo user_id = misma quota
        Total esperado: ~10% aceptados, ~90% bloqueados
        """
        print("\n" + "=" * 60)
        print("ESCENARIO 2: Ataque DDoS CON JWT (Rate Limiting por user_id)")
        print("=" * 60)
        print(f"Atacante usando MISMO user_id desde {self.num_ips} IPs")
        print(f"Requests por IP: {self.requests_per_ip}")
        print(f"Total requests: {self.total_requests}")
        print("-" * 60)

        self.results = {'accepted': 0, 'blocked': 0, 'errors': 0, 'latencies': []}
        token = self.load_attacker_token()

        with ThreadPoolExecutor(max_workers=self.num_ips) as executor:
            futures = []

            for ip in self.fake_ips:
                for _ in range(self.requests_per_ip):
                    futures.append(executor.submit(self.send_request, ip, token))

            for i, future in enumerate(as_completed(futures)):
                if (i + 1) % 100 == 0:
                    print(f"  Progreso: {i + 1}/{self.total_requests} requests enviados")

        return self._generate_report("CON_JWT")

    def _generate_report(self, scenario: str) -> dict:
        """Genera reporte de resultados"""
        total = self.results['accepted'] + self.results['blocked']
        avg_latency = sum(self.results['latencies']) / len(self.results['latencies']) if self.results['latencies'] else 0

        report = {
            'scenario': scenario,
            'timestamp': datetime.now().isoformat(),
            'config': {
                'num_ips': self.num_ips,
                'requests_per_ip': self.requests_per_ip,
                'total_requests': self.total_requests
            },
            'results': {
                'accepted': self.results['accepted'],
                'blocked': self.results['blocked'],
                'errors': self.results['errors'],
                'acceptance_rate': round(self.results['accepted'] / total * 100, 2) if total > 0 else 0,
                'block_rate': round(self.results['blocked'] / total * 100, 2) if total > 0 else 0,
                'avg_latency_ms': round(avg_latency, 2)
            },
            'effectiveness': self._evaluate_effectiveness(scenario)
        }

        self._print_report(report)
        return report

    def _evaluate_effectiveness(self, scenario: str) -> dict:
        """Evalúa la efectividad del control arquitectónico"""
        total = self.results['accepted'] + self.results['blocked']
        block_rate = self.results['blocked'] / total * 100 if total > 0 else 0

        if scenario == "CON_JWT":
            # Con JWT esperamos alto bloqueo (>80%)
            if block_rate >= 80:
                verdict = "EFECTIVO"
                description = "Rate limiting por user_id previene bypass exitosamente"
            elif block_rate >= 50:
                verdict = "PARCIALMENTE_EFECTIVO"
                description = "Rate limiting funciona pero con margen de mejora"
            else:
                verdict = "INEFECTIVO"
                description = "El atacante logró bypass del rate limiting"
        else:
            # Sin JWT esperamos bajo bloqueo (<20%)
            if block_rate < 20:
                verdict = "VULNERABLE"
                description = "Rate limiting por IP es vulnerable a DDoS distribuido"
            else:
                verdict = "PARCIALMENTE_PROTEGIDO"
                description = "Algo de protección, pero no suficiente"

        return {
            'verdict': verdict,
            'description': description,
            'block_rate': round(block_rate, 2)
        }

    def _print_report(self, report: dict):
        """Imprime reporte formateado"""
        print("\n" + "=" * 60)
        print(f"RESULTADOS - Escenario: {report['scenario']}")
        print("=" * 60)
        print(f"  Total requests enviados: {report['config']['total_requests']}")
        print(f"  Requests aceptados:      {report['results']['accepted']} ({report['results']['acceptance_rate']}%)")
        print(f"  Requests bloqueados:     {report['results']['blocked']} ({report['results']['block_rate']}%)")
        print(f"  Errores:                 {report['results']['errors']}")
        print(f"  Latencia promedio:       {report['results']['avg_latency_ms']} ms")
        print("-" * 60)
        print(f"  EVALUACIÓN: {report['effectiveness']['verdict']}")
        print(f"  {report['effectiveness']['description']}")
        print("=" * 60)


def run_full_experiment():
    """Ejecuta el experimento completo comparando ambos escenarios"""
    print("\n" + "#" * 70)
    print("# EXPERIMENTO: Evaluación de Rate Limiting contra DDoS Distribuido")
    print("#" * 70)
    print("\nHIPÓTESIS ARQUITECTÓNICA:")
    print("'El uso de rate limiting basado en identidad del usuario en el")
    print("API Gateway mejora la protección contra ataques de denegación")
    print("de servicio distribuidos en arquitecturas de microservicios.'")
    print("\n" + "#" * 70)

    # Resetear métricas
    try:
        requests.post("http://localhost:5000/api/metrics/reset")
    except:
        pass

    simulator = DDoSSimulator(num_ips=10, requests_per_ip=50)

    # Ejecutar ambos escenarios
    report_without_jwt = simulator.run_attack_without_jwt()

    print("\n⏳ Esperando 60 segundos para resetear rate limits...")
    time.sleep(60)

    report_with_jwt = simulator.run_attack_with_jwt()

    # Comparación final
    print("\n" + "#" * 70)
    print("# COMPARACIÓN FINAL")
    print("#" * 70)
    print("\n| Escenario      | Aceptados | Bloqueados | Efectividad    |")
    print("|----------------|-----------|------------|----------------|")
    print(f"| Sin JWT (IP)   | {report_without_jwt['results']['acceptance_rate']:>7}%  | {report_without_jwt['results']['block_rate']:>8}%  | {report_without_jwt['effectiveness']['verdict']:<14} |")
    print(f"| Con JWT (user) | {report_with_jwt['results']['acceptance_rate']:>7}%  | {report_with_jwt['results']['block_rate']:>8}%  | {report_with_jwt['effectiveness']['verdict']:<14} |")

    print("\n" + "#" * 70)
    print("# CONCLUSIÓN DEL EXPERIMENTO")
    print("#" * 70)

    if report_with_jwt['results']['block_rate'] > report_without_jwt['results']['block_rate'] + 50:
        print("\n✓ HIPÓTESIS VALIDADA:")
        print("  Rate limiting basado en user_id (JWT) es significativamente")
        print("  más efectivo que rate limiting por IP contra DDoS distribuido.")
    else:
        print("\n✗ HIPÓTESIS NO VALIDADA:")
        print("  Los resultados no muestran diferencia significativa.")

    # Guardar resultados
    results = {
        'experiment_date': datetime.now().isoformat(),
        'hypothesis': 'Rate limiting por user_id mejora protección contra DDoS distribuido',
        'scenarios': {
            'without_jwt': report_without_jwt,
            'with_jwt': report_with_jwt
        }
    }

    with open('experiment_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Resultados guardados en experiment_results.json")

    return results


if __name__ == '__main__':
    run_full_experiment()
