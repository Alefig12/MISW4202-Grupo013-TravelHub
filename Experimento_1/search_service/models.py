from . import db
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

class Accommodation(db.Model):
    __tablename__ = 'accommodations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(300))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    price_per_night = db.Column(db.Float)
    rating = db.Column(db.Float)
    amenities = db.Column(db.String(500))
    room_type = db.Column(db.String(50))
    max_guests = db.Column(db.Integer)
    available = db.Column(db.Boolean, default=True)

class AccommodationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Accommodation
        load_instance = True
