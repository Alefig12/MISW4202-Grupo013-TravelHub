"""
Tests automatizados para validar la hipótesis arquitectónica

Hipótesis: Rate limiting por user_id previene DDoS distribuido
"""
import pytest
import requests
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_gateway.auth import generate_jwt

BASE_URL = "http://localhost:5000"

class TestRateLimitingEffectiveness:
    """Tests para validar efectividad del rate limiting"""

    def test_rate_limit_blocks_after_quota(self):
        """
        Test: Después de 100 requests, el usuario debe ser bloqueado
        """
        token = generate_jwt('test-user-001', role='free')
        headers = {'Authorization': f'Bearer {token}'}

        accepted = 0
        blocked = 0

        # Enviar 150 requests (quota es 100/min)
        for i in range(150):
            response = requests.get(
                f"{BASE_URL}/api/accommodations/1",
                headers=headers
            )

            if response.status_code == 200:
                accepted += 1
            elif response.status_code == 429:
                blocked += 1

        # Esperamos ~100 aceptados y ~50 bloqueados
        assert accepted <= 110, f"Demasiados aceptados: {accepted}"
        assert blocked >= 40, f"Muy pocos bloqueados: {blocked}"

        print(f"✓ Test passed: {accepted} aceptados, {blocked} bloqueados")

    def test_multiple_ips_same_user_blocked(self):
        """
        Test: Múltiples IPs con el MISMO user_id deben compartir quota
        """
        token = generate_jwt('attacker-shared', role='free')

        accepted_total = 0
        blocked_total = 0

        # Simular 5 IPs diferentes, cada una enviando 50 requests
        for ip_suffix in range(1, 6):
            fake_ip = f"10.0.0.{ip_suffix}"
            headers = {
                'Authorization': f'Bearer {token}',
                'X-Forwarded-For': fake_ip
            }

            for _ in range(50):
                response = requests.get(
                    f"{BASE_URL}/api/accommodations/1",
                    headers=headers
                )

                if response.status_code == 200:
                    accepted_total += 1
                elif response.status_code == 429:
                    blocked_total += 1

        # Total: 250 requests desde 5 IPs con mismo user_id
        # Esperamos: ~100 aceptados (quota), ~150 bloqueados
        total = accepted_total + blocked_total
        block_rate = blocked_total / total * 100

        assert block_rate >= 50, f"Block rate muy bajo: {block_rate}%"

        print(f"✓ Test passed: {accepted_total} aceptados, {blocked_total} bloqueados ({block_rate:.1f}% bloqueado)")

    def test_different_users_independent_quota(self):
        """
        Test: Usuarios diferentes deben tener quotas independientes
        """
        results = {}

        for user_num in range(1, 4):
            token = generate_jwt(f'independent-user-{user_num}', role='free')
            headers = {'Authorization': f'Bearer {token}'}

            accepted = 0
            for _ in range(50):
                response = requests.get(
                    f"{BASE_URL}/api/accommodations/1",
                    headers=headers
                )
                if response.status_code == 200:
                    accepted += 1

            results[f'user-{user_num}'] = accepted

        # Cada usuario debe poder hacer ~50 requests (dentro de quota)
        for user, accepted in results.items():
            assert accepted >= 45, f"{user} bloqueado prematuramente: {accepted}/50"

        print(f"✓ Test passed: Usuarios independientes: {results}")

    def test_jwt_overhead_acceptable(self):
        """
        Test: El overhead de validación JWT debe ser < 50ms
        """
        token = generate_jwt('latency-test-user', role='free')
        headers = {'Authorization': f'Bearer {token}'}

        latencies = []

        for _ in range(20):
            start = time.time()
            requests.get(
                f"{BASE_URL}/api/accommodations/1",
                headers=headers
            )
            latencies.append((time.time() - start) * 1000)

        avg_latency = sum(latencies) / len(latencies)

        assert avg_latency < 50, f"Latencia muy alta: {avg_latency}ms"

        print(f"✓ Test passed: Latencia promedio: {avg_latency:.2f}ms")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
