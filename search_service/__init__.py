from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(instance_id=1):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel_hub.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['INSTANCE_ID'] = instance_id
    db.init_app(app)
    return app
