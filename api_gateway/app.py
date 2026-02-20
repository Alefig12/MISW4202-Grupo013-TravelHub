from flask import Flask, jsonify
from flask_restful import Api, Resource
from celery import Celery

app = Flask(__name__)
api = Api(app)

celery_app = Celery(
    'api_gateway',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
)

class AccommodationResource(Resource):
    def get(self, accommodation_id):
        try:
            task = celery_app.send_task(
                'search_service.get_accommodation',
                args=[accommodation_id],
                queue='QueriesQueue'
            )
            result = task.get(timeout=10)

            if result['status'] == 'success':
                return result['data'], 200
            else:
                return {'error': result['message']}, 404

        except Exception as e:
            return {'error': f'Service unavailable: {str(e)}'}, 503

class HealthResource(Resource):
    def get(self):
        return {'status': 'API Gateway is running'}, 200

api.add_resource(AccommodationResource, '/api/accommodation/<int:accommodation_id>')
api.add_resource(HealthResource, '/api/health')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
