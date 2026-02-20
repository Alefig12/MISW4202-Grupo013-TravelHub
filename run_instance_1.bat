@echo off
echo Starting SearchService Instance 1...
set INSTANCE_ID=1
celery -A search_service.tasks:celery_app worker -l info -Q QueriesQueue,HealthQueue_1 --pool=solo -n worker1@%%h
