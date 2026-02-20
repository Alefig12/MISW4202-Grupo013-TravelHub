@echo off
echo Seeding database with 1000 accommodations...
python -m search_service.seed_db
echo Done!
pause
