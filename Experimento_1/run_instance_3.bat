@echo off
echo Starting SearchService Instance 3...
set INSTANCE_ID=3
celery -A search_service.tasks:celery_app worker -l info -Q QueriesQueue,HealthQueue_3 --pool=solo -n worker3@%%h
