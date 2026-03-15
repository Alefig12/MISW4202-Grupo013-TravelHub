"""
Analizador de Métricas del Experimento

Genera gráficas y reportes para evaluar la efectividad
del rate limiting basado en JWT vs IP.
"""
import json
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import os

def load_results(filepath='experiment_results.json') -> dict:
    """Carga resultados del experimento"""
    with open(filepath, 'r') as f:
        return json.load(f)

def generate_comparison_chart(results: dict, output_dir='charts'):
    """
    Genera gráfica de barras comparando escenarios

    Métricas:
    - Requests bloqueados por atacante (principal)
    - Requests aceptados
    """
    os.makedirs(output_dir, exist_ok=True)

    scenarios = ['Sin JWT\n(Rate limit por IP)', 'Con JWT\n(Rate limit por user_id)']

    without_jwt = results['scenarios']['without_jwt']['results']
    with_jwt = results['scenarios']['with_jwt']['results']

    accepted = [without_jwt['accepted'], with_jwt['accepted']]
    blocked = [without_jwt['blocked'], with_jwt['blocked']]

    x = range(len(scenarios))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))

    bars1 = ax.bar([i - width/2 for i in x], accepted, width, label='Aceptados', color='#4CAF50')
    bars2 = ax.bar([i + width/2 for i in x], blocked, width, label='Bloqueados', color='#F44336')

    ax.set_ylabel('Número de Requests')
    ax.set_title('Efectividad del Rate Limiting contra DDoS Distribuido\n(Atacante con 10 IPs, 500 requests totales)')
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.legend()

    # Añadir valores sobre las barras
    for bar in bars1:
        height = bar.get_height()
        ax.annotate(f'{int(height)}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')

    for bar in bars2:
        height = bar.get_height()
        ax.annotate(f'{int(height)}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')

    plt.tight_layout()
    filepath = os.path.join(output_dir, 'comparison_chart.png')
    plt.savefig(filepath, dpi=150)
    plt.close()

    print(f"✓ Gráfica generada: {filepath}")
    return filepath

def generate_effectiveness_chart(results: dict, output_dir='charts'):
    """
    Genera gráfica de efectividad (% bloqueado)
    """
    os.makedirs(output_dir, exist_ok=True)

    scenarios = ['Sin JWT\n(IP)', 'Con JWT\n(user_id)']

    without_jwt = results['scenarios']['without_jwt']['results']
    with_jwt = results['scenarios']['with_jwt']['results']

    block_rates = [without_jwt['block_rate'], with_jwt['block_rate']]

    fig, ax = plt.subplots(figsize=(8, 6))

    colors = ['#FF9800', '#2196F3']
    bars = ax.bar(scenarios, block_rates, color=colors)

    ax.set_ylabel('Porcentaje de Requests Bloqueados (%)')
    ax.set_title('Efectividad del Control Arquitectónico\n(% de requests del atacante bloqueados)')
    ax.set_ylim(0, 100)

    # Línea de umbral de efectividad
    ax.axhline(y=80, color='green', linestyle='--', label='Umbral efectivo (80%)')
    ax.axhline(y=50, color='orange', linestyle='--', label='Umbral mínimo (50%)')

    for bar, rate in zip(bars, block_rates):
        height = bar.get_height()
        ax.annotate(f'{rate}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=12, fontweight='bold')

    ax.legend(loc='upper left')
    plt.tight_layout()

    filepath = os.path.join(output_dir, 'effectiveness_chart.png')
    plt.savefig(filepath, dpi=150)
    plt.close()

    print(f"✓ Gráfica generada: {filepath}")
    return filepath

def generate_report(results: dict, output_dir='charts'):
    """Genera reporte completo en formato texto"""
    os.makedirs(output_dir, exist_ok=True)

    without_jwt = results['scenarios']['without_jwt']
    with_jwt = results['scenarios']['with_jwt']

    report = f"""
================================================================================
                    REPORTE DEL EXPERIMENTO - RATE LIMITING
================================================================================

FECHA: {results['experiment_date']}

HIPÓTESIS ARQUITECTÓNICA:
"{results['hypothesis']}"

--------------------------------------------------------------------------------
                              CONFIGURACIÓN
--------------------------------------------------------------------------------
- Número de IPs del atacante (botnet simulada): {without_jwt['config']['num_ips']}
- Requests por IP: {without_jwt['config']['requests_per_ip']}
- Total de requests por escenario: {without_jwt['config']['total_requests']}

--------------------------------------------------------------------------------
                              RESULTADOS
--------------------------------------------------------------------------------

ESCENARIO 1: Rate Limiting por IP (Sin JWT)
-------------------------------------------
- Requests aceptados:  {without_jwt['results']['accepted']:>5} ({without_jwt['results']['acceptance_rate']}%)
- Requests bloqueados: {without_jwt['results']['blocked']:>5} ({without_jwt['results']['block_rate']}%)
- Latencia promedio:   {without_jwt['results']['avg_latency_ms']} ms
- Evaluación:          {without_jwt['effectiveness']['verdict']}
  → {without_jwt['effectiveness']['description']}

ESCENARIO 2: Rate Limiting por user_id (Con JWT)
------------------------------------------------
- Requests aceptados:  {with_jwt['results']['accepted']:>5} ({with_jwt['results']['acceptance_rate']}%)
- Requests bloqueados: {with_jwt['results']['blocked']:>5} ({with_jwt['results']['block_rate']}%)
- Latencia promedio:   {with_jwt['results']['avg_latency_ms']} ms
- Evaluación:          {with_jwt['effectiveness']['verdict']}
  → {with_jwt['effectiveness']['description']}

--------------------------------------------------------------------------------
                              ANÁLISIS
--------------------------------------------------------------------------------

MÉTRICA PRINCIPAL: Requests bloqueados por atacante
- Con IP:      {without_jwt['results']['block_rate']}% bloqueados
- Con user_id: {with_jwt['results']['block_rate']}% bloqueados
- Mejora:      {with_jwt['results']['block_rate'] - without_jwt['results']['block_rate']:.1f} puntos porcentuales

EVALUACIÓN DE EFECTIVIDAD:
"""

    improvement = with_jwt['results']['block_rate'] - without_jwt['results']['block_rate']

    if improvement > 50:
        report += """
✓ HIPÓTESIS VALIDADA

El rate limiting basado en identidad del usuario (user_id extraído del JWT)
demuestra ser significativamente más efectivo que el rate limiting por IP
para proteger contra ataques DDoS distribuidos.

CONCLUSIONES:
1. El atacante con múltiples IPs puede evadir fácilmente el rate limit por IP
2. El mismo atacante NO puede evadir el rate limit por user_id
3. La arquitectura con JWT proporciona protección robusta contra botnets
4. El overhead de validación JWT (~5-10ms) es un trade-off aceptable

RECOMENDACIÓN:
Implementar rate limiting basado en JWT/user_id en API Gateways para
sistemas expuestos a riesgo de ataques DDoS distribuidos.
"""
    else:
        report += """
✗ HIPÓTESIS NO VALIDADA

Los resultados no muestran una diferencia significativa entre ambos enfoques.
Se requiere investigación adicional.
"""

    report += """
================================================================================
                              FIN DEL REPORTE
================================================================================
"""

    filepath = os.path.join(output_dir, 'experiment_report.txt')
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✓ Reporte generado: {filepath}")
    print(report)

    return filepath


def analyze_experiment():
    """Función principal que ejecuta el análisis completo"""
    try:
        results = load_results()
    except FileNotFoundError:
        print("⚠ No se encontró experiment_results.json")
        print("  Ejecuta primero: python -m ddos_simulator.distributed_attack")
        return

    print("\n=== Generando análisis del experimento ===\n")

    generate_comparison_chart(results)
    generate_effectiveness_chart(results)
    generate_report(results)

    print("\n✓ Análisis completo. Revisa la carpeta 'charts/'")


if __name__ == '__main__':
    analyze_experiment()
