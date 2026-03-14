"""
Módulo de autenticación JWT para el experimento de Rate Limiting
"""
from jose import jwt, JWTError
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import json
import os

# Generar claves RSA dinámicamente para el experimento
def generate_rsa_keys():
    """Genera par de claves RSA para firmar JWT"""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    return private_pem, public_pem

# Claves globales (se generan una vez al iniciar)
PRIVATE_KEY, PUBLIC_KEY = generate_rsa_keys()

def generate_jwt(user_id: str, role: str = 'free') -> str:
    """
    Genera token JWT con claims de usuario

    Args:
        user_id: Identificador único del usuario (clave para rate limiting)
        role: 'free' (100 req/min) o 'premium' (1000 req/min)

    Returns:
        JWT token firmado con RS256
    """
    payload = {
        'user_id': user_id,
        'role': role,
        'permissions': ['search_accommodations'],
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=1)
    }

    token = jwt.encode(payload, PRIVATE_KEY, algorithm='RS256')
    return token

def validate_jwt(token: str) -> dict:
    """
    Valida y decodifica un token JWT

    Returns:
        Payload del token si es válido

    Raises:
        JWTError: Si el token es inválido
    """
    return jwt.decode(token, PUBLIC_KEY, algorithms=['RS256'])

def generate_attacker_tokens(num_attackers: int = 1) -> dict:
    """
    Genera tokens para simular atacantes

    Args:
        num_attackers: Número de atacantes diferentes

    Returns:
        Dict con tokens por atacante
    """
    tokens = {}
    for i in range(num_attackers):
        attacker_id = f"attacker-{i+1:03d}"
        tokens[attacker_id] = generate_jwt(attacker_id, role='free')
    return tokens

def generate_legitimate_tokens(num_users: int = 10) -> dict:
    """
    Genera tokens para usuarios legítimos
    """
    tokens = {}
    for i in range(num_users):
        user_id = f"user-{i+1:03d}"
        role = 'premium' if i < 2 else 'free'  # 2 premium, resto free
        tokens[user_id] = generate_jwt(user_id, role=role)
    return tokens

if __name__ == '__main__':
    # Generar tokens de prueba
    print("=== Generando tokens para el experimento ===\n")

    # Token de atacante (1 solo user_id, usará múltiples IPs)
    attacker_tokens = generate_attacker_tokens(1)
    print("Token del atacante (user_id único):")
    print(f"  attacker-001: {attacker_tokens['attacker-001'][:50]}...")

    # Tokens de usuarios legítimos
    legitimate_tokens = generate_legitimate_tokens(5)
    print("\nTokens de usuarios legítimos:")
    for user_id, token in legitimate_tokens.items():
        print(f"  {user_id}: {token[:50]}...")

    # Guardar tokens en archivo
    all_tokens = {
        'attacker': attacker_tokens,
        'legitimate': legitimate_tokens,
        'public_key': PUBLIC_KEY
    }

    tokens_path = os.path.join(os.path.dirname(__file__), '..', 'tokens.json')
    with open(tokens_path, 'w') as f:
        json.dump(all_tokens, f, indent=2)

    print(f"\n✓ Tokens guardados en {tokens_path}")
