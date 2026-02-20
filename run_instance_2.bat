@echo off
echo Starting SearchService Instance 2...
set INSTANCE_ID=2
celery -A search_service.tasks:celery_app worker -l info -Q QueriesQueue,HealthQueue_2 --pool=solo -n worker2@%%h
