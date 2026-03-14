import time
import redis
from datetime import datetime
from celery import Celery

celery_app = Celery(
    'heartbeat_monitor',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

redis_client = redis.Redis(host='localhost', port=6379, db=2, decode_responses=True)

INSTANCES = ['1', '2', '3']
HEALTH_CHECK_INTERVAL = 5
TIMEOUT = 3

class HeartbeatMonitor:
    def __init__(self):
        self.instance_status = {inst: 'unknown' for inst in INSTANCES}

    def check_instance_health(self, instance_id):
        try:
            task = celery_app.send_task(
                'search_service.health_check',
                queue=f'HealthQueue_{instance_id}'
            )
            result = task.get(timeout=TIMEOUT)

            if result and result.get('status') == 'healthy':
                return True, result
        except Exception as e:
            print(f"[{datetime.now()}] Instance {instance_id} health check failed: {e}")
        return False, None

    def update_instance_status(self, instance_id, is_healthy):
        previous_status = self.instance_status[instance_id]
        new_status = 'healthy' if is_healthy else 'unhealthy'
        self.instance_status[instance_id] = new_status

        redis_client.hset('instance_status', instance_id, new_status)
        redis_client.set(f'instance_{instance_id}_last_check', datetime.now().isoformat())

        if previous_status != new_status:
            if new_status == 'unhealthy':
                print(f"[{datetime.now()}] ALERT: Instance {instance_id} is DOWN!")
            else:
                print(f"[{datetime.now()}] Instance {instance_id} is back UP!")

    def run(self):
        print(f"[{datetime.now()}] Heartbeat Monitor started")
        print(f"Monitoring {len(INSTANCES)} instances with {HEALTH_CHECK_INTERVAL}s interval")
        print("-" * 50)

        while True:
            print(f"\n[{datetime.now()}] Running health checks...")

            for instance_id in INSTANCES:
                is_healthy, result = self.check_instance_health(instance_id)
                self.update_instance_status(instance_id, is_healthy)

                status = "HEALTHY" if is_healthy else "UNHEALTHY"
                print(f"  Instance {instance_id}: {status}")

            healthy_count = sum(1 for s in self.instance_status.values() if s == 'healthy')
            print(f"  Summary: {healthy_count}/{len(INSTANCES)} instances healthy")

            time.sleep(HEALTH_CHECK_INTERVAL)

if __name__ == '__main__':
    monitor = HeartbeatMonitor()
    monitor.run()
