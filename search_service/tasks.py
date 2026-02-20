import os
from celery import Celery

INSTANCE_ID = os.environ.get('INSTANCE_ID', '1')

celery_app = Celery(
    'search_service',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)

@celery_app.task(name='search_service.get_accommodation')
def get_accommodation(accommodation_id):
    from . import create_app, db
    from .models import Accommodation, AccommodationSchema

    app = create_app(int(INSTANCE_ID))
    with app.app_context():
        accommodation = Accommodation.query.get(accommodation_id)
        if accommodation:
            schema = AccommodationSchema()
            result = schema.dump(accommodation)
            result['served_by_instance'] = INSTANCE_ID
            return {'status': 'success', 'data': result}
        return {'status': 'error', 'message': 'Accommodation not found'}

@celery_app.task(name='search_service.health_check')
def health_check():
    return {
        'status': 'healthy',
        'instance_id': INSTANCE_ID,
        'service': 'SearchService'
    }
